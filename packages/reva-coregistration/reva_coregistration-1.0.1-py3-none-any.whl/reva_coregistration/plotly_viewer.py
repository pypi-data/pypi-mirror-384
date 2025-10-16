import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from reva_coregistration.coordinates import get_associated_coordinates_from_any_viewer

pyo.init_notebook_mode(connected=True)

VIEWER_CONTENT_TO_LABEL = {
    'L': 'MicroCT MAP Image (L)',
    'R': 'Photo Image (R)',
    'C': 'Warped MicroCT MAP Image (C)'
}

class PlotlyGridViewer:
    def __init__(self, microct_img, photo_img, warped_img):
        """
        Initialize the PlotlyGridViewer with four images for 2x2 grid layout.
        
        Args:
            microct_img: PIL Image for top-left (L)
            photo_img: PIL Image for top-right (R) 
            warped_img: PIL Image for bottom-left (C)
        """
        self.microct_img = microct_img
        self.photo_img = photo_img
        self.warped_img = warped_img
        
        # Convert PIL images to numpy arrays for plotly
        self.microct_array = np.array(microct_img)
        self.photo_array = np.array(photo_img)
        self.warped_array = np.array(warped_img)
        
        # Get image dimensions
        self.target_height, self.target_width = self.microct_array.shape[:2]
        self.source_height, self.source_width = self.photo_array.shape[:2]
        
        self.fig = None
        self.create_figure()
    
    def add_image_to_viewer(self, image, viewer_id, col, row):
        self.fig.add_trace(
            go.Image(z=image, name=VIEWER_CONTENT_TO_LABEL[viewer_id]),
            row=row, col=col
        )

    def create_figure(self):
        """Create the 2x2 subplot figure with all images"""
        # Create subplots
        self.fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('MicroCT MAP Image (L)', 'Photo Image (R)', 
                          'Warped MicroCT MAP Image (C)'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Add images to subplots
        # Top left - MicroCT (L)
        self.add_image_to_viewer(self.microct_array, 'L', 1, 1)
        
        # Top right - Photo (R)
        self.add_image_to_viewer(self.photo_array, 'R', 2, 1)
        
        # Bottom left - Warped MicroCT (C)
        self.add_image_to_viewer(self.warped_array, 'C', 1, 2)
        
        # Update layout
        self.fig.update_layout(
            title="Image Grid Viewer",
            width=1200,
            height=800,
            showlegend=False
        )
        
        # Update axes
        for i in range(1, 3):
            for j in range(1, 3):
                if i == 2 and j == 2:
                    continue
                self.fig.update_xaxes(showgrid=False, zeroline=False, row=i, col=j)
                self.fig.update_yaxes(showgrid=False, zeroline=False, row=i, col=j)
    
    def show(self):
        """Display the visualization"""
        self.fig.show()


class PlotlyCrosshairViewer(PlotlyGridViewer):
    def __init__(self, microct_img, photo_img, warped_microct_img, as_microct_map, coords):
        self.as_microct_map = as_microct_map
        self.coords = coords
        super().__init__(microct_img, photo_img, warped_microct_img)
        
        # Recreate the figure with crosshairs
        self.create_figure()


    def add_image_to_viewer(self, image, viewer_id, col, row):
        ''' Add an image to the viewer. If coordinates exist for the viewer_id, add crosshairs overlay at that location. '''
        self.fig.add_trace(
            go.Image(z=image, name=VIEWER_CONTENT_TO_LABEL[viewer_id]),
            row=row, col=col
        )
        
        # Check if coordinates exist for this viewer_id
        if viewer_id in self.coords:
            x_pixel = self.coords[viewer_id]['x']
            y_pixel = self.coords[viewer_id]['y']
            
            
            self.fig.add_trace(
                go.Scatter(
                    x=[x_pixel],
                    y=[y_pixel],
                    mode='markers',
                    marker=dict(size=10, color='red', symbol='cross'),
                    showlegend=False
                ),
                row=row, col=col
            )
