import tkinter as tk
import warnings
from dataclasses import dataclass
from tkinter import messagebox, ttk

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

warnings.filterwarnings("ignore", category=UserWarning)


@dataclass
class GlobalScaling:
    min: float
    max: float
    p1: float
    p99: float
    lower: float
    upper: float


class ImageSlideViewer:
    """
    An interactive image viewer for multidimensional numpy arrays.

    Features:
    - Navigate through image stack with slider
    - Support for complex arrays (magnitude, phase, real, imaginary)
    - Contrast and level adjustment controls
    - Colormap selection
    - Image information display
    """

    def __init__(self, image_stack, title="Image Slide Viewer"):
        """
        Initialize the image viewer.

        Parameters:
        -----------
        image_stack : numpy.ndarray
            multidimensional numpy array
        title : str
            Window title
        """

        self.shape = image_stack.shape

        self.image_stack = np.reshape(
            image_stack, (self.shape[0], self.shape[1], -1), order="F"
        )
        self.original_stack = self.image_stack.copy()
        self.title = title

        self.n_images = self.image_stack.shape[2]
        self.current_index = 0

        # Check if array is complex
        self.is_complex = np.iscomplexobj(self.image_stack)

        # Display options for complex arrays
        self.complex_display_options = ["magnitude", "phase", "real", "imaginary"]
        self.current_complex_display = "magnitude" if self.is_complex else "real"

        # Calculate global min/max for consistent scaling across all images
        self.global_scaling = {}  # Always use dict structure for consistency
        self.calculate_global_scaling()  # Initialize GUI

        # Image display parameters
        self.level = self.get_global_scale_for_current_mode().p99
        self.vmin = None
        self.vmax = None

        self.setup_gui()
        self.update_display()

    def as_fortran(self, data):
        if not data.flags.f_contiguous:
            return np.asfortranarray(data)
        return data

    def z_index_to_multidim_indices(self, z_index):
        """
        Convert a z-index from the reshaped 3D array back to original multidimensional indices.

        Parameters:
        -----------
        z_index : int
            Index in the flattened z-dimension (0 to n_images-1)

        Returns:
        --------
        tuple
            Multidimensional indices corresponding to the original array shape

        Example:
        --------
        If original shape was (2, 3, 4, 100, 100) and you reshaped to (100, 100, 24),
        then z_index=5 would return the indices (0, 1, 1) for the original (2, 3, 4) dimensions.
        """
        if z_index < 0 or z_index >= self.n_images:
            raise ValueError(f"z_index {z_index} is out of bounds [0, {self.n_images})")

        # Get the shape of dimensions that were flattened (exclude the last 2 spatial dimensions)
        flattened_shape = self.shape[2:]

        # Convert flat index back to multidimensional indices using numpy's unravel_index
        multidim_indices = np.unravel_index(z_index, flattened_shape, order="F")

        # Ensure result is always a tuple, even for single dimensions
        if not isinstance(multidim_indices, tuple):
            multidim_indices = (multidim_indices,)

        return multidim_indices

    def multidim_indices_to_z_index(self, multidim_indices):
        """
        Convert multidimensional indices back to z-index in the reshaped 3D array.

        Parameters:
        -----------
        multidim_indices : tuple
            Indices for the original multidimensional array (excluding last 2 spatial dims)

        Returns:
        --------
        int
            Corresponding z-index in the flattened array

        Example:
        --------
        If original shape was (2, 3, 4, 100, 100) and multidim_indices=(0, 1, 1),
        this would return z_index=5.
        """
        # Get the shape of dimensions that were flattened
        flattened_shape = self.shape[:-2]

        # Validate indices
        if len(multidim_indices) != len(flattened_shape):
            raise ValueError(
                f"Expected {len(flattened_shape)} indices, got {len(multidim_indices)}"
            )

        for i, (idx, dim_size) in enumerate(zip(multidim_indices, flattened_shape)):
            if idx < 0 or idx >= dim_size:
                raise ValueError(
                    f"Index {idx} is out of bounds for dimension {i} with size {dim_size}"
                )

        # Convert multidimensional indices to flat index using numpy's ravel_multi_index
        z_index = np.ravel_multi_index(multidim_indices, flattened_shape)

        return z_index

    def get_current_multidim_indices(self):
        """
        Get the current multidimensional indices for the currently displayed image.

        Returns:
        --------
        tuple
            Current multidimensional indices
        """
        return self.z_index_to_multidim_indices(self.current_index)

    def calculate_global_scaling(self):
        """
        Calculate global min/max values for consistent scaling across all images.
        This ensures that brightness/contrast is consistent across the entire volume.
        """
        if self.is_complex:
            # For complex arrays, calculate scaling for each display mode
            for mode in self.complex_display_options:
                if mode == "magnitude":
                    values = np.abs(self.image_stack)
                elif mode == "phase":
                    values = np.angle(self.image_stack)
                elif mode == "real":
                    values = np.real(self.image_stack)
                elif mode == "imaginary":
                    values = np.imag(self.image_stack)

                # Calculate percentiles for robust scaling
                p1, p99 = np.percentile(values, [1, 99])
                self.global_scaling[mode] = GlobalScaling(
                    min=float(np.min(values)),
                    max=float(np.max(values)),
                    p1=float(p1),
                    p99=float(p99),
                    lower=float(p1),
                    upper=float(p99),
                )
        else:
            # For real arrays, calculate single scaling and store under 'real' key
            p1, p99 = np.percentile(self.image_stack, [1, 99])
            self.global_scaling["real"] = GlobalScaling(
                min=float(np.min(self.image_stack)),
                max=float(np.max(self.image_stack)),
                p1=float(p1),
                p99=float(p99),
                lower=float(p1),
                upper=float(p99),
            )

    def get_global_scale_for_current_mode(self):
        """
        Get the appropriate global min/max values for the current display mode.

        Returns:
        --------
        tuple
            (vmin, vmax) for the current display mode
        """
        return self.global_scaling[self.current_complex_display]

    def set_global_scale_for_current_mode(self, lower=None, upper=None):
        """
        Set the appropriate global min/max values for the current display mode.
        """
        if self.is_complex:
            key = self.current_complex_display
        else:
            key = "real"

        if lower is not None:
            self.global_scaling[key].lower = lower
            if lower > self.global_scaling[key].upper:
                self.global_scaling[key].lower = self.global_scaling[key].upper - 1e-5
        if upper is not None:
            self.global_scaling[key].upper = upper
            if upper < self.global_scaling[key].lower:
                self.global_scaling[key].upper = self.global_scaling[key].lower + 1e-5

    def setup_gui(self):
        """Setup the GUI components."""
        self.root = tk.Tk()
        self.root.title(self.title)

        # Create main frame with minimal padding
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Create control panel at the top (without navigation)
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        # Create matplotlib figure with tight layout
        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor="white")
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_position((0.0, 0.0, 1.0, 1.0))  # Fill entire figure area

        # Pack bottom widgets first (important for tkinter layout)
        # Status bar at very bottom
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            font=("Arial", 8),
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 2))

        # Navigation panel above status bar (without frame)
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(2, 0))

        # Image slider
        ttk.Label(nav_frame, text="").grid(row=0, column=0, sticky=tk.W)
        self.image_slider = ttk.Scale(
            nav_frame,
            from_=0,
            to=self.n_images - 1,
            orient=tk.HORIZONTAL,
            command=self.on_image_change,
        )
        self.image_slider.grid(row=0, column=1, sticky=tk.EW, padx=(5, 5))

        # Image index label
        self.index_label = ttk.Label(nav_frame, text=f"1 / {self.n_images}")
        self.index_label.grid(row=0, column=2, sticky=tk.W)

        nav_frame.columnconfigure(1, weight=1)

        # Create canvas last so it fills remaining space
        self.canvas = FigureCanvasTkAgg(self.fig, main_frame)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # All controls in a single horizontal frame
        col = 0  # Track column position

        # Complex array controls (if applicable)
        if self.is_complex:
            self.complex_var = tk.StringVar(value=self.current_complex_display)
            self.complex_combo = ttk.Combobox(
                control_frame,
                textvariable=self.complex_var,
                values=self.complex_display_options,
                state="readonly",
                width=10,
            )
            self.complex_combo.grid(row=0, column=col, sticky=tk.W, padx=(5, 10))
            col += 1

            # Use both event binding and trace for robustness
            self.complex_combo.bind(
                "<<ComboboxSelected>>", self.on_complex_display_change
            )
            self.complex_var.trace("w", self.on_complex_var_change)

        # Colormap selection
        self.colormap_var = tk.StringVar(value="gray")
        colormap_combo = ttk.Combobox(
            control_frame,
            textvariable=self.colormap_var,
            values=[
                "gray",
                "viridis",
                "plasma",
                "inferno",
                "magma",
                "hot",
                "cool",
                "spring",
                "summer",
                "autumn",
                "winter",
            ],
            state="readonly",
            width=10,
        )
        colormap_combo.grid(row=0, column=col, sticky=tk.W, padx=(5, 5))
        col += 1
        colormap_combo.bind("<<ComboboxSelected>>", self.on_colormap_change)

        # Level control
        scaling = self.get_global_scale_for_current_mode()
        ttk.Label(control_frame, text="Level:").grid(
            row=0, column=col, sticky=tk.W, padx=(0, 5)
        )
        col += 1

        self.level_slider = ttk.Scale(
            control_frame,
            from_=scaling.min,
            to=scaling.max,
            orient=tk.HORIZONTAL,
            command=self.on_level_change,
            length=60,
        )
        self.level_slider.grid(row=0, column=col, sticky=tk.EW, padx=(0, 5))
        col += 1

        self.level_label = ttk.Label(control_frame, text="1.00")
        self.level_label.grid(row=0, column=col, sticky=tk.W, padx=(0, 5))
        col += 1

        # Reset button
        ttk.Button(
            control_frame, text="Reset", command=self.reset_display, width=6
        ).grid(row=0, column=col, sticky=tk.W, padx=(0, 5))
        col += 1

        # Make the level slider column expandable
        level_col = (
            3 if self.is_complex else 2
        )  # Level slider column (updated position)
        control_frame.columnconfigure(level_col, weight=1)

        # Bind keyboard events
        self.root.bind("<Left>", lambda e: self.navigate_image(-1))
        self.root.bind("<Right>", lambda e: self.navigate_image(1))
        self.root.bind("<Prior>", lambda e: self.navigate_image(-10))  # Page Up
        self.root.bind("<Next>", lambda e: self.navigate_image(10))  # Page Down
        self.root.bind("<Home>", lambda e: self.set_image_index(0))
        self.root.bind("<End>", lambda e: self.set_image_index(self.n_images - 1))

        self.root.focus_set()  # Enable keyboard focus

        # Set initial values after all GUI elements are created
        self.set_initial_values()

        # Set window size based on image dimensions
        self.root.update_idletasks()  # Ensure all widgets are sized

        # Calculate window size based on image dimensions
        image_height, image_width = self.image_stack.shape[:2]

        # Add space for controls and padding
        control_height = 80  # Space for top controls, navigation, and status bar
        padding = 0  # General padding

        # Calculate desired window size
        aspect_ratio = image_width / image_height if image_height > 0 else 1
        window_width = max(400, image_width + padding)  # Minimum 400px width
        window_height = max(
            control_height + 50,
            int(window_width / aspect_ratio + control_height + padding),
        )
        # Set a reasonable maximum to prevent huge windows
        max_width = min(1200, window_width)
        max_height = min(900, window_height)

        # Remove fixed minimum size constraint and set initial size based on image
        self.root.geometry(f"{max_width}x{max_height}")

    def set_initial_values(self):
        """Set initial slider values after GUI is fully created."""
        self.image_slider.set(0)
        self.level_slider.set(self.get_global_scale_for_current_mode().p99)

    def get_display_image(self):
        """Get the current image to display based on complex display settings."""
        current_image = self.image_stack[:, :, self.current_index]

        if self.is_complex:
            if self.current_complex_display == "magnitude":
                display_image = np.abs(current_image)
            elif self.current_complex_display == "phase":
                display_image = np.angle(current_image)
            elif self.current_complex_display == "real":
                display_image = np.real(current_image)
            elif self.current_complex_display == "imaginary":
                display_image = np.imag(current_image)
        else:
            display_image = current_image

        # Handle multi-channel images (convert to grayscale if needed)
        if display_image.ndim == 3 and display_image.shape[2] > 1:
            display_image = np.mean(display_image, axis=2)

        return display_image

    def update_display(self):
        """Update the image display."""
        try:
            # Get current image
            display_image = self.get_display_image()

            # Get global scaling for current display mode
            scaling = self.get_global_scale_for_current_mode()

            # Clear and plot
            self.ax.clear()

            im = self.ax.imshow(
                display_image,
                cmap=self.colormap_var.get(),
                vmin=scaling.lower,
                vmax=scaling.upper,
                aspect="equal",
                interpolation="nearest",
            )

            self.ax.axis("off")

            # Remove all margins and borders - ensure tight fit
            self.ax.set_position((0.0, 0.0, 1.0, 1.0))
            self.ax.margins(0)
            self.ax.set_xlim(0, display_image.shape[1])
            self.ax.set_ylim(
                display_image.shape[0], 0
            )  # Invert y-axis for image display

            # Update status with slice info
            min_val, max_val = np.min(display_image), np.max(display_image)
            shape_str = f"{display_image.shape[0]}x{display_image.shape[1]}"
            # Get multidimensional indices for current image
            multidim_indices = self.get_current_multidim_indices()
            indices_str = f"[:, :, {', '.join(map(str, multidim_indices))}]"

            slice_info = f"Index {indices_str} ({shape_str})"
            self.status_var.set(
                f"{slice_info} | Min: {min_val:.3f}, Max: {max_val:.3f}, Type: {display_image.dtype}"
            )

            self.canvas.draw()

        except Exception as e:
            messagebox.showerror("Display Error", f"Error updating display: {str(e)}")

    def on_image_change(self, value):
        """Handle image slider change."""
        self.current_index = int(float(value))
        self.index_label.config(text=f"{self.current_index + 1} / {self.n_images}")
        self.update_display()

    def on_complex_display_change(self, event):
        """Handle complex display mode change."""
        self.current_complex_display = self.complex_var.get()
        self.update_display()

    def on_complex_var_change(self, *args):
        """Callback when complex_var StringVar changes."""
        # This provides a backup method for detecting changes
        # in case the ComboboxSelected event doesn't fire properly
        if hasattr(self, "current_complex_display"):
            if self.complex_var.get() != self.current_complex_display:
                self.current_complex_display = self.complex_var.get()
                self.update_display()

    def on_level_change(self, value):
        """Handle level slider change."""
        self.level = float(value)
        self.set_global_scale_for_current_mode(upper=self.level)
        if hasattr(self, "level_label"):
            self.level_label.config(text=f"{self.level:.2f}")
        self.update_display()

    def on_colormap_change(self, event):
        """Handle colormap change."""
        self.update_display()

    def navigate_image(self, step):
        """Navigate to relative image index."""
        new_index = self.current_index + step
        self.set_image_index(new_index)

    def set_image_index(self, index):
        """Set absolute image index."""
        index = max(0, min(index, self.n_images - 1))
        self.image_slider.set(index)
        self.on_image_change(index)

    def reset_display(self):
        """Reset all display parameters to defaults."""
        self.contrast = 1.0
        self.brightness = 0.0
        self.vmin = None
        self.vmax = None

        self.level_slider.set(self.get_global_scale_for_current_mode().p99)
        self.colormap_var.set("gray")

        if self.is_complex:
            self.current_complex_display = "magnitude"
            self.complex_var.set("magnitude")

        self.update_display()

    def auto_contrast(self):
        """Auto-adjust contrast - choice between global and current image scaling."""
        # Ask user whether to use global or current image scaling
        choice = messagebox.askyesnocancel(
            "Auto Contrast",
            "Use global scaling for entire volume?\n\n"
            "Yes: Global scaling (consistent across all images)\n"
            "No: Current image scaling\n"
            "Cancel: No change",
        )

        if choice is None:  # Cancel
            return
        elif choice:  # Yes - Global scaling
            # Use global scaling (reset to default global range)
            self.vmin = None
            self.vmax = None
            messagebox.showinfo(
                "Auto Contrast",
                "Using global scaling for entire volume.\n"
                "All images will have consistent brightness/contrast.",
            )
        else:  # No - Current image scaling
            current_image = self.get_display_image()
            # Calculate percentiles for current image
            p1, p99 = np.percentile(current_image, [1, 99])

            if p99 > p1:
                # Set vmin/vmax based on current image percentiles
                self.vmin = p1
                self.vmax = p99
                messagebox.showinfo(
                    "Auto Contrast",
                    f"Contrast adjusted to current image range [{p1:.3f}, {p99:.3f}]",
                )
            else:
                messagebox.showwarning(
                    "Auto Contrast", "Current image has no variation in values."
                )

        self.update_display()

    def show_image_info(self):
        """Show detailed information about the current image."""
        current_image = self.get_display_image()
        original_image = self.image_stack[self.current_index]

        info = f"""Image Information:
        
Index: {self.current_index + 1} / {self.n_images}
Shape: {original_image.shape}
Data Type: {original_image.dtype}
Complex: {self.is_complex}

Current Display ({self.current_complex_display if self.is_complex else 'real'}):
  Shape: {current_image.shape}
  Min: {np.min(current_image):.6f}
  Max: {np.max(current_image):.6f}
  Mean: {np.mean(current_image):.6f}
  Std: {np.std(current_image):.6f}

Display Settings:
  Contrast: {self.contrast:.2f}
  Brightness: {self.brightness:.2f}
  Colormap: {self.colormap_var.get()}
"""

        messagebox.showinfo("Image Information", info)

    def run(self):
        """Start the image viewer."""
        self.root.mainloop()


def image_slide(image_stack, title="Image Slide Viewer"):
    """Launch the image slide viewer with given image stack."""
    viewer = ImageSlideViewer(image_stack, title)
    viewer.run()
