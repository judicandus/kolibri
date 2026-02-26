from django.templatetags.static import static

from kolibri.core import theme_hook
from kolibri.plugins import KolibriPluginBase
from kolibri.plugins.hooks import register_hook


class AngelsThemePlugin(KolibriPluginBase):
    pass


@register_hook
class AngelsThemeHook(theme_hook.ThemeHook):
    @property
    def theme(self):
        return {
            # Brand color scales generated from primary (#213953) and secondary (#a6c52e)
            # Use https://materialpalettes.com/ to fine-tune
            "brandColors": {
                "primary": {
                    "v_100": "#d4dce4",
                    "v_200": "#a9b9c9",
                    "v_300": "#7e96ae",
                    "v_400": "#537393",
                    "v_500": "#213953",
                    "v_600": "#1a2e43",
                },
                "secondary": {
                    "v_100": "#eef5d5",
                    "v_200": "#d6e89e",
                    "v_300": "#bfdb67",
                    "v_400": "#b3d44b",
                    "v_500": "#a6c52e",
                    "v_600": "#859e25",
                },
            },
            # Sign-in page configuration
            "signIn": {
                # Temporary: using a placeholder until high-res image is provided
                "background": static("assets/angels_theme/login-background.jpg"),
                "topLogo": {
                    "src": static(
                        "assets/angels_theme/logo-angels-horizontal-dark.png"
                    ),
                    "style": "padding-left: 64px; padding-right: 64px; margin-bottom: 8px; margin-top: 8px",
                    "alt": "Angels for Education",
                },
                "title": "Angels Academy",
                "showTitle": True,
                "showKolibriFooterLogo": False,
                "showPoweredBy": True,
                "poweredByStyle": "color: #ffffff",
            },
            # App bar (top navigation bar)
            "appBar": {
                "background": "#213953",
                "textColor": "#ffffff",
                "topLogo": {
                    "src": static("assets/angels_theme/logo-icon-green.png"),
                    "style": "max-height: 36px; margin-right: 8px",
                    "alt": "Angels Academy",
                },
            },
            # Side navigation menu
            "sideNav": {
                "title": "Angels Academy",
                "topLogo": {
                    "src": static(
                        "assets/angels_theme/logo-academy-horizontal-green.png"
                    ),
                    "style": "max-height: 48px; margin: 12px auto; display: block",
                    "alt": "Angels Academy",
                },
                "showKolibriFooterLogo": False,
                "brandedFooter": {
                    "logo": {
                        "src": static(
                            "assets/angels_theme/logo-angels-horizontal-dark.png"
                        ),
                        "style": "max-height: 32px",
                        "alt": "Angels for Education",
                    },
                    "paragraphArray": [],
                },
            },
            # Favicon and PWA icons
            "logos": [
                {
                    "src": static("assets/angels_theme/logo-icon-green.png"),
                    "content_type": "image/png",
                    "size": "512x512",
                },
                {
                    "src": static("assets/angels_theme/logo-icon-green.png"),
                    "content_type": "image/png",
                    "size": "192x192",
                },
            ],
        }
