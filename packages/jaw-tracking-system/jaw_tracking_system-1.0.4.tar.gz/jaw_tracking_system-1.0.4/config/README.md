# JawTrackingSystem (JTS) Configuration 
Various configurations for the JawTrackingSystem (JTS) can be easily managed through `JSON` files.
These files allow you to customize the system's behavior, such as the motion capture data source, 
analysis parameters, output settings, and visualization options.

---

## Configuration Example with Comments
The following JSON configuration file provides a comprehensive example of how to set up the JTS for jaw motion analysis
with a Qualisys motion capture system.

```json
{
  "data_source": {                        // Source and mode of motion capture data
    "type": "qualisys",                   // Type of system, e.g., "qualisys" or future types
    "mode": "offline",                    // "offline" (file-based) or "streaming" (real-time)
    "filename": "path/data.mat",          // Path to data file (required for "offline" mode)
      
    "streaming": {                        // Streaming configuration (if mode is "streaming")
      "host": "127.0.0.1",                // Host IP for streaming server
      "port": 22223,                      // Port for streaming server
      "version": "1.25",                  // Protocol version
      "buffer_size": 1000,                // Number of frames to buffer
      "timeout": 5,                       // Connection timeout in seconds
      "components": ["3d", "6d", "6deuler"], // Data components to stream
      "stream_rate": "allframes"          // Stream rate: "allframes" or specific frequency
    }
  },
    
  "analysis": {                           // Settings for analysis pipeline
    "description": "Jaw motion analysis experiment", // Description of the experiment
      
    "calibration": {                      // Calibration configuration for landmarks
      "mode": "offline",                  // "offline" or "online" calibration
        
      "online_config": {                  // Online calibration parameters
        "method": "button_triggered",     // Calibration method: "button_triggered", "automatic", or "guided"
        "stability_threshold": 0.5,       // Threshold for tool stability (mm)
        "stability_duration": 0.5,        // Duration required for stable tool (seconds)
        "capture_window": 1.0,            // Time window for capturing frames (seconds)
        "auto_capture_delay": 0.5,        // Delay before auto-capture after stability (seconds, for "automatic" mode)
        "post_capture_delay": 2.0,        // Delay after capture before next landmark (seconds, for "automatic")
        "require_confirmation": true,     // Whether to require user confirmation for capture
        "calibration_tool_name": "CT",    // Name of the calibration tool rigid body
          
        "feedback": {                     // Feedback settings for user
          "visual": true,                 // Enable visual feedback
          "audio": true,                  // Enable audio feedback
          "voice_prompts": false          // Enable voice prompts (not implemented by default)
        },
          
        "landmarks": {                    // Groups of anatomical landmarks to calibrate
          "mandibular": ["mand_point_1", "mand_point_2", "mand_point_3"],
          "maxillary": ["max_point_1", "max_point_2", "max_point_3"]
        }
      },
        
      "mandibular": {                     // Mandibular calibration details
        "rigid_bodies": ["MP", "CT"],     // Rigid bodies used for mandibular calibration
        "points": [                       // Points and frame intervals for calibration
          {
            "name": "mand_point_1",
            "frame_interval": [2100, 2600]
          },
          {
            "name": "mand_point_2",
            "frame_interval": [5100, 5600]
          },
          {
            "name": "mand_point_3",
            "frame_interval": [7500, 8000]
          }
        ]
      },
        
      "maxillary": {                      // Maxillary calibration details
        "rigid_bodies": ["HP", "CT"],     // Rigid bodies used for maxillary calibration
        "points": [                       // Points and frame intervals for calibration
          {
            "name": "max_point_1",
            "frame_interval": [9500, 10000]
          },
          {
            "name": "max_point_2",
            "frame_interval": [12100, 12600]
          },
          {
            "name": "max_point_3",
            "frame_interval": [14200, 14700]
          }
        ]
      }
    },
      
    "experiment": {                       // Main experiment configuration
      "frame_interval": [15300, 27000],   // Frame interval for the main experiment
      "use_sub_experiments": false,       // Whether to use sub-experiments
      "combine_sub_experiments": ["open_close", "chewing"], // Names of sub-experiments to combine
        
      "sub_experiments": {                // Sub-experiment definitions
        "open_close": [15300, 18400],     // Sub-experiment name and frame interval
        "left_right": [20050, 21850],
        "protrusion_retrusion": [21851, 23950],
        "chewing": [24400, 26051],
        "complex_motion": [               // Multiple intervals for complex motion
          [27000, 27500],
          [28000, 28500],
          [29000, 29500]
        ]
      },
        
      "interpolation": {                  // Settings for connecting frame intervals
        "method": "cubic",                // Interpolation method: "linear", "cubic", "slerp", "hermite", "none"
        "transition_frames": 10,          // Number of frames for smooth transitions
        "connect_intervals": true         // Whether to connect intervals with interpolation
      },
        
      "relative_motion": {                // Relative motion configuration
        "reference_body": "HP",           // Reference rigid body (e.g., maxillary head)
        "moving_body": "MP"               // Moving rigid body (e.g., mandibular point)
      },
        
      "coordinate_transform": {           // Coordinate system registration
        "enabled": true,                  // Whether to perform coordinate transformation
        "calibration_type": "maxillary",  // Which calibration points to use for registration
        "model_points": [                 // Model points corresponding to calibration points (in model coordinates)
          [-0.244678, -109.416, 101.356],
          [23.6189, -106.201, 73.9031],
          [-24.0445, -106.078, 74.1795]
        ]
      },
        
      "smoothing": {                      // Trajectory smoothing settings
        "enabled": true,                  // Whether to apply smoothing
        "window_length": 11,              // Window length for Savitzky-Golay filter
        "poly_order": 3                   // Polynomial order for filter
      },
        
      "coordinate_origin_index": 0        // Index of calibration point to use as origin
    },
      
    "visualization": {                    // Visualization settings
      "raw_data": true,                   // Show raw data plots
      "raw_data_3d": false,               // Show raw data in 3D
      "calibration_transforms": true,     // Visualize calibration transformations
      "relative_marker_motion": true,     // Show relative marker motion plots
      "landmark_motion": true,            // Show landmark motion plots
      "final_trajectory": true,           // Show final trajectory plots
      "plot_2d_components": true,         // Plot 2D trajectory components
      "plot_export_only": true,           // Only plot the trajectory to be exported
      "plot_rot_3d": false,               // Show 3D rotation visualization
      "show_plots": true,                 // Whether to display plots (interactive)
      "use_tex_font": false,              // Use LaTeX fonts in plots
        
      "plot_style": {                     // Plot style parameters
        "sample_rate": 10,                // Subsampling rate for plotting
        "linewidth": 1.5,                 // Line width for plots
        "axes_label_fontsize": 12,        // Font size for axes labels
        "axes_tick_fontsize": 10,         // Font size for axes ticks
        "title_fontsize": 14,             // Font size for title
        "legend_fontsize": 10,            // Font size for legend
        "figure_size": [12, 8],           // Figure size (width, height) in inches
        "labelpad_scale": 0.7,            // Scale factor for label padding
          
        "view_3d": {                      // 3D view settings
          "elev": 30,                     // Elevation angle
          "azim": 0,                      // Azimuth angle
          "roll": 0,                      // Roll angle
          "vertical_axis": "y"            // Vertical axis
        },
          
        "colors": ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown"], // Color palette
        "line_styles": ["-", "--", "-.", ":"], // Line styles
          
        "grid": {                         // Grid settings
          "enabled": true,                // Enable grid
          "alpha": 0.3                    // Grid transparency
        }
      }
    }
  },
    
  "output": {                             // Output settings
    "directory": "./analysis_results",    // Output directory for results
    "save_csv": true,                     // Save trajectory as CSV
    "save_hdf5": true,                    // Save trajectory as HDF5
    "save_plots": false,                  // Save plots as images
    "save_tikz": false,                   // Save plots as TikZ (for LaTeX)
    "csv_filename": "jaw_motion",         // Base name for CSV output
    "hdf5_filename": "jaw_motion.h5",     // Name for HDF5 output file
    "store_quaternions": true,            // Store rotations as quaternions in HDF5
    "derivative_order": 2,                // Maximum derivative order to compute and store
    "scale_factor": 0.001,                // Scale factor for output units (e.g., mm to m)
    "unit": "m"                           // Output unit for translations
  }
}
```