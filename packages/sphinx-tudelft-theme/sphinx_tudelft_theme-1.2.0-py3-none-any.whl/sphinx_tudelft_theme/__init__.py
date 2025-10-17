import os

from sphinx.application import Sphinx
from sphinx.util.fileutil import copy_asset_file

try:
    from sphinx_tudelft_theme._version import version as __version__
except ImportError:
    __version__ = "1.0.0"

def copy_stylesheet(app: Sphinx, exc: None) -> None:
    base_dir = os.path.dirname(__file__)
    style = os.path.join(base_dir, 'static', 'tudelft_style.css')
    if app.config.tud_change_fonts:
        fonts = os.path.join(base_dir, 'static', 'tudelft_fonts.css')
        fonts_src_dir2 = os.path.join(base_dir, 'static', 'RobotoSlab-Regular.woff2')
        fonts_src_dir = os.path.join(base_dir, 'static', 'RobotoSlab-Regular.woff')
    if app.config.tud_sticky_logo:
        sticky = os.path.join(base_dir, 'static', 'sticky-logo.css')
    if app.config.tud_change_titlesize:
        title = os.path.join(base_dir, 'static', 'tudelft_title.css')
    
    if app.builder.format == 'html' and not exc:
        static_dir = os.path.join(app.builder.outdir, '_static')

        copy_asset_file(style, static_dir)
        if app.config.tud_change_fonts:
            print('Copying TU Delft fonts')
            copy_asset_file(fonts, static_dir)
            copy_asset_file(fonts_src_dir2, static_dir)
            copy_asset_file(fonts_src_dir, static_dir)
        if app.config.tud_sticky_logo:
            print('Copying sticky logo CSS')
            copy_asset_file(sticky, static_dir)
        if app.config.tud_change_titlesize:
            print('Copying TU Delft title styling')
            copy_asset_file(title, static_dir)            

def copy_logos(app: Sphinx, exc: None) -> None:
    if app.config.tud_change_logo:
        base_dir = os.path.dirname(__file__)
        light = os.path.join(base_dir, 'static', 'TUDelft_logo_descriptor_rgb.png')
        dark = os.path.join(base_dir, 'static', 'TUDelft_logo_descriptor_white.png')
        
        if app.builder.format == 'html' and not exc:
            static_dir = os.path.join(app.builder.outdir, '_static')
            copy_asset_file(light, static_dir)
            copy_asset_file(dark, static_dir)

def set_logo(app,conf) -> None:
    if conf.tud_change_logo:
        print('Changing logo to TU Delft logo')
        old =  app.config.html_theme_options
        if 'logo' in old:
            old['logo'] = old['logo'] | {'image_light':'TUDelft_logo_descriptor_rgb.png','image_dark': 'TUDelft_logo_descriptor_white.png'}
        else:
            old['logo'] = {'image_light':'TUDelft_logo_descriptor_rgb.png','image_dark': 'TUDelft_logo_descriptor_white.png'}
        app.config.html_theme_options = old
    else:
        print('Using user-defined logo')

def copy_favicon(app: Sphinx, exc: None) -> None:
    if app.config.tud_change_favicon:
        base_dir = os.path.dirname(__file__)
        favicon = os.path.join(base_dir, 'static', 'TUD_favicon.svg')

        if app.builder.format == 'html' and not exc:
            static_dir = os.path.join(app.builder.outdir, '_static')

            copy_asset_file(favicon, static_dir)

def set_favicon(app,conf):
    if conf.tud_change_favicon:
        print('Changing favicon to TU Delft favicon')
        old =  app.config
        old['favicons'] = {"rel": "icon", "href": "TUD_favicon.svg", "type": "image/svg+xml"}
        app.config = old
    else:
        print('Using user-defined favicon')

def set_mtext(app,conf):
    if conf.tud_change_mtext:
        print('Changing mtext font to inherited from html')
        old =  app.config
        
        if 'mathjax3_config' in old:
            old_mj = old.mathjax3_config
            if old_mj is None:
                old['mathjax3_config'] = {'chtml': {'mtextInheritFont': True}}
            elif 'chtml' in old_mj:
                old.mathjax3_config['chtml'] = old.mathjax3_config['chtml'] | {'mtextInheritFont': True}
            else:
                old.mathjax3_config['chtml'] = {'mtextInheritFont': True}         
        else:
            old['mathjax3_config'] = {'chtml': {'mtextInheritFont': True}}
            
        app.config = old
    else:
        print('Using default/user defined mtext font')

def setup(app: Sphinx):
    app.setup_extension('sphinx_favicon')
    app.add_config_value('tud_change_logo', True, 'env')
    app.add_config_value('tud_change_favicon', True, 'env')
    app.add_config_value('tud_change_fonts', True, 'env')
    app.add_config_value('tud_change_mtext', True, 'env')
    app.add_config_value('tud_sticky_logo', True, 'env')
    app.add_config_value('tud_change_titlesize', True, 'env')
    app.add_css_file('tudelft_style.css')
    app.add_css_file('tudelft_fonts.css')
    app.add_css_file('sticky-logo.css')
    app.add_css_file('tudelft_title.css')
    app.connect('build-finished', copy_stylesheet)
    app.connect('build-finished', copy_logos)
    app.connect('build-finished', copy_favicon)
    app.connect('config-inited',set_logo)
    app.connect('config-inited',set_favicon)
    app.connect('config-inited',set_mtext)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }