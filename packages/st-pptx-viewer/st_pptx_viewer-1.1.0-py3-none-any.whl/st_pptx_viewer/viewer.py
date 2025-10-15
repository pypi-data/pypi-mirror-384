"""
Core viewer component for st_pptx_viewer module.

Provides a configurable Streamlit component that renders PPTX files using PptxViewJS library.
"""

import base64
from pathlib import Path
from typing import Optional, Union, BinaryIO
from dataclasses import dataclass, field
import streamlit as st
import streamlit.components.v1 as components


@dataclass
class PptxViewerConfig:
    """Configuration options for the PPTX viewer component.
    
    Attributes:
        width: Canvas width in pixels (default: 960)
        height: Canvas height in pixels. If None, calculated from aspect ratio
        show_toolbar: Whether to show navigation toolbar (default: True)
        show_slide_counter: Whether to show slide counter (default: True)
        initial_slide: Initial slide index to display (0-based, default: 0)
        enable_keyboard: Enable keyboard navigation (arrows, pgup/pgdn) (default: True)
        toolbar_position: Position of toolbar ('top' or 'bottom', default: 'top')
        canvas_border: CSS border style for canvas (default: '1px solid #ddd')
        canvas_background: Background color for canvas (default: '#fff')
        canvas_border_radius: Border radius in pixels (default: 4)
        component_height: Total component height. If None, auto-calculated
        custom_css: Additional custom CSS styles
        pptxviewjs_path: Path to PptxViewJS.min.js bundle. If None, uses default
        enable_fullscreen: Show fullscreen button (default: False)
        toolbar_style: CSS style dict for toolbar customization
    """
    width: int = 960
    height: Optional[int] = None
    show_toolbar: bool = True
    show_slide_counter: bool = True
    initial_slide: int = 0
    enable_keyboard: bool = True
    toolbar_position: str = 'top'
    canvas_border: str = '1px solid #ddd'
    canvas_background: str = '#fff'
    canvas_border_radius: int = 4
    component_height: Optional[int] = None
    custom_css: str = ''
    pptxviewjs_path: Optional[Union[str, Path]] = None
    enable_fullscreen: bool = False
    toolbar_style: dict = field(default_factory=dict)


def pptx_viewer(
    pptx_file: Union[bytes, BinaryIO, str, Path],
    config: Optional[PptxViewerConfig] = None,
    key: Optional[str] = None
) -> None:
    """
    Display a PPTX file in Streamlit using PptxViewJS.
    
    Args:
        pptx_file: PPTX file as bytes, file-like object, or path to file
        config: PptxViewerConfig instance with display options. If None, uses defaults
        key: Unique key for the component (for Streamlit state management)
    
    Example:
        >>> import streamlit as st
        >>> from st_pptx_viewer import pptx_viewer, PptxViewerConfig
        >>> 
        >>> uploaded = st.file_uploader("Upload PPTX", type=["pptx"])
        >>> if uploaded:
        >>>     config = PptxViewerConfig(
        >>>         width=1200,
        >>>         show_toolbar=True,
        >>>         enable_keyboard=True
        >>>     )
        >>>     pptx_viewer(uploaded, config=config)
    """
    if config is None:
        config = PptxViewerConfig()
    
    # Read file data
    if isinstance(pptx_file, (str, Path)):
        with open(pptx_file, 'rb') as f:
            data = f.read()
    elif hasattr(pptx_file, 'read'):
        data = pptx_file.read()
    else:
        data = pptx_file
    
    # Encode PPTX data
    b64_pptx = base64.b64encode(data).decode("ascii")
    
    # Determine PptxViewJS source (CDN or custom path)
    if config.pptxviewjs_path:
        # Custom local bundle specified
        bundle_path = Path(config.pptxviewjs_path)
        if not bundle_path.exists():
            st.error(
                f"PptxViewJS bundle not found at {bundle_path}. "
                "Please check the path in pptxviewjs_path config."
            )
            st.stop()
        bundle_base64 = base64.b64encode(bundle_path.read_bytes()).decode("ascii")
        use_cdn = False
    else:
        # Use CDN by default
        use_cdn = True
        bundle_base64 = None
    
    # Calculate dimensions
    canvas_width = config.width
    canvas_height = config.height if config.height else int(canvas_width * 9 / 16)
    
    # Build toolbar HTML
    toolbar_html = ""
    if config.show_toolbar:
        toolbar_styles = {
            'padding': '8px',
            'border-bottom': '1px solid #eee' if config.toolbar_position == 'top' else 'none',
            'border-top': '1px solid #eee' if config.toolbar_position == 'bottom' else 'none',
            'display': 'flex',
            'gap': '8px',
            'align-items': 'center',
            'background': '#f8f9fa'
        }
        toolbar_styles.update(config.toolbar_style)
        toolbar_style_str = '; '.join(f'{k}: {v}' for k, v in toolbar_styles.items())
        
        status_html = '<span id="status" class="status"></span>' if config.show_slide_counter else ''
        fullscreen_btn = '<button id="fullscreen">⛶ Fullscreen</button>' if config.enable_fullscreen else ''
        
        toolbar_html = f"""
        <div class="toolbar" style="{toolbar_style_str}">
          <button id="prev">◀ Prev</button>
          <button id="next">Next ▶</button>
          {fullscreen_btn}
          {status_html}
        </div>
        """
    
    # Build CSS
    base_css = f"""
    body {{ margin:0; font-family: system-ui, -apple-system, Segoe UI, Arial, sans-serif; overflow:hidden; }}
    .toolbar button {{ 
      padding: 6px 12px; 
      border: 1px solid #ccc; 
      border-radius: 4px; 
      background: #fff; 
      cursor: pointer;
      font-size: 14px;
    }}
    .toolbar button:hover {{ background: #f0f0f0; }}
    .toolbar button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
    #canvas {{ 
      border: {config.canvas_border}; 
      border-radius: {config.canvas_border_radius}px; 
      background: {config.canvas_background}; 
      display: block; 
      max-width: 100%;
      height: auto;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }}
    .status {{ color:#666; font-size:12px; margin-left:auto; }}
    .wrap {{ padding: 10px; max-width: 100%; }}
    
    /* Fullscreen styles - based on full.html reference */
    body:fullscreen {{
      background: #000 !important;
      margin: 0 !important;
      padding: 0 !important;
    }}
    body:-webkit-full-screen {{
      background: #000 !important;
      margin: 0 !important;
      padding: 0 !important;
    }}
    body:-moz-full-screen {{
      background: #000 !important;
      margin: 0 !important;
      padding: 0 !important;
    }}
    
    /* Fullscreen wrap container - center content using positioning */
    body:fullscreen .wrap {{
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      padding: 0 !important;
      margin: 0 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      background: #000 !important;
    }}
    body:-webkit-full-screen .wrap {{
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      padding: 0 !important;
      margin: 0 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      background: #000 !important;
    }}
    body:-moz-full-screen .wrap {{
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      padding: 0 !important;
      margin: 0 !important;
      display: flex !important;
      align-items: center !important;
      justify-content: center !important;
      background: #000 !important;
    }}
    
    /* Fullscreen canvas - maximize while maintaining aspect ratio */
    body:fullscreen #canvas {{
      position: relative !important;
      max-width: 100vw !important;
      max-height: 100vh !important;
      border: none !important;
      border-radius: 0 !important;
      box-shadow: none !important;
    }}
    body:-webkit-full-screen #canvas {{
      position: relative !important;
      max-width: 100vw !important;
      max-height: 100vh !important;
      border: none !important;
      border-radius: 0 !important;
      box-shadow: none !important;
    }}
    body:-moz-full-screen #canvas {{
      position: relative !important;
      max-width: 100vw !important;
      max-height: 100vh !important;
      border: none !important;
      border-radius: 0 !important;
      box-shadow: none !important;
    }}
    
    /* Hide toolbar in fullscreen mode for clean presentation */
    body:fullscreen .toolbar {{
      display: none !important;
    }}
    body:-webkit-full-screen .toolbar {{
      display: none !important;
    }}
    body:-moz-full-screen .toolbar {{
      display: none !important;
    }}
    """
    
    final_css = base_css + config.custom_css
    
    # Build keyboard navigation JS
    keyboard_js = ""
    if config.enable_keyboard:
        keyboard_js = """
        document.addEventListener('keydown', function(e) {
          // Don't interfere with fullscreen ESC/F11 keys
          if (e.key === 'Escape' || e.key === 'F11') {
            return;
          }
          
          // Navigation keys
          if (e.key === 'ArrowLeft' || e.key === 'ArrowUp' || e.key === 'PageUp') {
            e.preventDefault();
            if (prev && !prev.disabled) prev.click();
          } else if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === 'PageDown' || e.key === ' ') {
            e.preventDefault();
            if (next && !next.disabled) next.click();
          } else if (e.key === 'Home') {
            e.preventDefault();
            // Go to first slide
            if (viewer && viewer.render) {
              viewer.render(canvas, { slideIndex: 0 }).then(function() {
                if (prev) prev.disabled = true;
                if (next) next.disabled = false;
                updateStatus();
              });
            }
          } else if (e.key === 'End') {
            e.preventDefault();
            // Go to last slide
            if (viewer && viewer.render) {
              const lastSlide = viewer.getSlideCount() - 1;
              viewer.render(canvas, { slideIndex: lastSlide }).then(function() {
                if (prev) prev.disabled = false;
                if (next) next.disabled = true;
                updateStatus();
              });
            }
          }
        });
        """
    
    # Build fullscreen JS
    fullscreen_js = ""
    if config.enable_fullscreen:
        fullscreen_js = """
        const fullscreenBtn = document.getElementById('fullscreen');
        let isFullscreen = false;
        
        function enterFullscreen() {
          const container = document.body;
          if (container.requestFullscreen) {
            container.requestFullscreen();
          } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
          } else if (container.mozRequestFullScreen) {
            container.mozRequestFullScreen();
          }
        }
        
        function exitFullscreen() {
          if (document.exitFullscreen) {
            document.exitFullscreen();
          } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
          } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
          }
        }
        
        function handleFullscreenChange() {
          const isNowFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement);
          isFullscreen = isNowFullscreen;
          
          if (fullscreenBtn) {
            fullscreenBtn.textContent = isFullscreen ? '⛶ Exit Fullscreen' : '⛶ Fullscreen';
          }
          
          // Let CSS handle fullscreen sizing - just restore on exit
          if (!isFullscreen) {
            // Restore original sizing when exiting fullscreen
            // Re-apply aspect ratio from loaded presentation
            if (viewer && viewer.processor) {
              applyCanvasAspect(viewer);
            }
          }
        }
        
        if (fullscreenBtn) {
          fullscreenBtn.addEventListener('click', function() {
            if (!isFullscreen) {
              enterFullscreen();
            } else {
              exitFullscreen();
            }
          });
        }
        
        // Listen for fullscreen changes
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
        document.addEventListener('mozfullscreenchange', handleFullscreenChange);
        
        // Handle ESC key to exit fullscreen
        document.addEventListener('keydown', function(e) {
          if (e.key === 'Escape' && isFullscreen) {
            exitFullscreen();
          } else if (e.key === 'F11') {
            e.preventDefault();
            if (!isFullscreen) {
              enterFullscreen();
            } else {
              exitFullscreen();
            }
          }
        });
        """
    
    # Position content
    # Note: Canvas dimensions will be adjusted after loading based on actual slide aspect ratio
    # Initial size uses high-DPI scaling for quality
    initial_dpr = 2  # Default to 2x for quality, will be adjusted based on actual devicePixelRatio
    initial_canvas_width = canvas_width * initial_dpr
    initial_canvas_height = canvas_height * initial_dpr
    
    content_order = ""
    if config.toolbar_position == 'top':
        content_order = f"{toolbar_html}<div class='wrap'><canvas id='canvas' width='{initial_canvas_width}' height='{initial_canvas_height}' style='width:{canvas_width}px;height:{canvas_height}px'></canvas></div>"
    else:
        content_order = f"<div class='wrap'><canvas id='canvas' width='{initial_canvas_width}' height='{initial_canvas_height}' style='width:{canvas_width}px;height:{canvas_height}px'></canvas></div>{toolbar_html}"
    
    # Build script loading section
    if use_cdn:
        # Use CDN - simpler and no build required
        script_loading = """
      <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/pptxviewjs/dist/PptxViewJS.min.js"></script>
        """
        bundle_loader_js = """
          function loadBundle() {
            return Promise.resolve();  // CDN bundle already loaded
          }
        """
    else:
        # Use custom local bundle
        script_loading = """
      <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js"></script>
        """
        bundle_loader_js = f"""
          const bundleBase64 = "{bundle_base64}";
          
          function loadBundle() {{
            return new Promise(function(resolve, reject) {{
              try {{
                const binary = atob(bundleBase64);
                const len = binary.length;
                const bytes = new Uint8Array(len);
                for (let i = 0; i < len; i += 1) {{
                  bytes[i] = binary.charCodeAt(i);
                }}
                const blob = new Blob([bytes], {{ type: 'application/javascript' }});
                const url = URL.createObjectURL(blob);
                const script = document.createElement('script');
                script.type = 'application/javascript';
                script.onload = function() {{
                  URL.revokeObjectURL(url);
                  resolve();
                }};
                script.onerror = function(err) {{
                  URL.revokeObjectURL(url);
                  reject(err);
                }};
                script.src = url;
                document.head.appendChild(script);
              }} catch (err) {{
                reject(err);
              }}
            }});
          }}
        """
    
    # Generate HTML component
    html = f"""
    <!doctype html>
    <html>
    <head>
      <meta charset='utf-8' />
      <meta name='viewport' content='width=device-width, initial-scale=1' />
      <style>{final_css}</style>
    </head>
    <body>
      {script_loading}
      {content_order}
      <script>
        (function() {{
          {bundle_loader_js}
          
          const desiredWidth = {canvas_width};
          const initialSlide = {config.initial_slide};
          const canvas = document.getElementById('canvas');
          const prev = document.getElementById('prev');
          const next = document.getElementById('next');
          const status = document.getElementById('status');

          if (prev) prev.disabled = true;
          if (next) next.disabled = true;
          if (status) status.textContent = 'Loading viewer...';

          function postFrameHeight() {{
            try {{
              const bodyHeight = document.body ? document.body.scrollHeight : 600;
              const target = Math.max(bodyHeight + 40, desiredWidth * 0.75);
              window.parent.postMessage({{ type: 'streamlit:setFrameHeight', height: target }}, '*');
            }} catch (_err) {{}}
          }}

          function b64ToUint8Array(b64) {{
            const binary = atob(b64);
            const len = binary.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i += 1) {{
              bytes[i] = binary.charCodeAt(i);
            }}
            return bytes;
          }}

          function applyCanvasAspect(viewerInstance) {{
            const processor = viewerInstance && viewerInstance.processor;
            if (!processor || typeof processor.getSlideDimensions !== 'function') {{
              console.warn('[st_pptx_viewer] Cannot apply canvas aspect: processor not ready');
              return false;
            }}
            const dims = processor.getSlideDimensions();
            if (!dims || !dims.cx || !dims.cy) {{
              console.warn('[st_pptx_viewer] Cannot apply canvas aspect: slide dimensions not available');
              return false;
            }}
            
            // Calculate aspect ratio from actual slide dimensions
            const aspect = dims.cy / dims.cx;
            const targetWidth = desiredWidth;
            const targetHeight = Math.max(120, Math.round(targetWidth * aspect));
            
            // Use high-DPI scaling for crisp rendering
            const dpr = window.devicePixelRatio || 1;
            const scale = Math.max(1.5, dpr); // At least 1.5x for quality
            
            console.log('[st_pptx_viewer] Applying canvas sizing:', {{
              slideEMU: {{ cx: dims.cx, cy: dims.cy }},
              aspectRatio: aspect.toFixed(3),
              targetCSS: {{ width: targetWidth, height: targetHeight }},
              devicePixelRatio: dpr,
              scale: scale,
              canvasBuffer: {{ width: Math.round(targetWidth * scale), height: Math.round(targetHeight * scale) }}
            }});
            
            // Set CSS display size
            canvas.style.width = targetWidth + 'px';
            canvas.style.height = targetHeight + 'px';
            
            // Set canvas buffer size with high-DPI scaling
            canvas.width = Math.round(targetWidth * scale);
            canvas.height = Math.round(targetHeight * scale);
            
            // Scale the canvas context
            const ctx = canvas.getContext('2d');
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.scale(scale, scale);
            
            const wrap = document.querySelector('.wrap');
            if (wrap) {{
              wrap.style.width = targetWidth + 'px';
              wrap.style.maxWidth = targetWidth + 'px';
            }}
            postFrameHeight();
            
            console.log('[st_pptx_viewer] Canvas sizing applied successfully');
            return true;
          }}

          loadBundle()
            .then(function() {{
              const api = window.PptxViewJS || {{}};
              const PPTXViewer = api.PPTXViewer;
              if (!PPTXViewer) {{
                throw new Error('PptxViewJS namespace not found after bundle load.');
              }}

              const viewer = new PPTXViewer({{ canvas }});

              function updateStatus() {{
                const total = viewer.getSlideCount();
                const idx = typeof viewer.getCurrentSlideIndex === 'function'
                  ? viewer.getCurrentSlideIndex()
                  : 0;
                if (status) {{
                  status.textContent = total ? 'Slide ' + (idx + 1) + ' / ' + total : '';
                }}
                if (prev) {{
                  prev.disabled = idx <= 0 || total <= 1;
                }}
                if (next) {{
                  next.disabled = idx >= total - 1 || total <= 1;
                }}
                postFrameHeight();
              }}

              viewer.on && viewer.on('renderComplete', function() {{
                updateStatus();
              }});

              const bytes = b64ToUint8Array('{b64_pptx}');
              viewer.loadFile(bytes)
                .then(function() {{
                  // Apply canvas dimensions based on actual slide aspect ratio
                  const aspectApplied = applyCanvasAspect(viewer);
                  if (!aspectApplied) {{
                    console.warn('Could not determine slide dimensions, using default aspect ratio');
                  }}
                  // Render with properly sized canvas
                  return viewer.render(canvas, {{ slideIndex: initialSlide }});
                }})
                .then(function() {{
                  updateStatus();
                  // Re-render after a short delay to capture any async chart rendering
                  setTimeout(function() {{
                    viewer.render(canvas, {{ slideIndex: initialSlide }}).catch(function() {{}});
                  }}, 250);
                }})
                .catch(function(err) {{
                  console.error(err);
                  if (status) status.textContent = 'Error rendering presentation';
                  postFrameHeight();
                }});

              if (prev) {{
                prev.addEventListener('click', function() {{
                  viewer.previousSlide(canvas).then(function() {{
                    updateStatus();
                  }});
                }});
              }}

              if (next) {{
                next.addEventListener('click', function() {{
                  viewer.nextSlide(canvas).then(function() {{
                    updateStatus();
                  }});
                }});
              }}

              {keyboard_js}
              {fullscreen_js}

              updateStatus();
              postFrameHeight();
            }})
            .catch(function(err) {{
              console.error(err);
              if (status) status.textContent = 'Failed to load viewer bundle';
              postFrameHeight();
            }});
        }})();
      </script>
    </body>
    </html>
    """
    
    # Calculate component height
    if config.component_height:
        component_height = config.component_height
    else:
        toolbar_height = 50 if config.show_toolbar else 0
        component_height = int(canvas_width * 0.75 + toolbar_height + 60)
    
    # Render component
    components.html(html, height=component_height, scrolling=False)

