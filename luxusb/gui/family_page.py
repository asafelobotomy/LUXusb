"""
Family selection page for distro wizard
"""

import logging
from luxusb.gui import Gtk, Adw, GLib
from typing import Any
import json
from pathlib import Path

from luxusb.constants import DistroFamily

logger = logging.getLogger(__name__)


class FamilySelectionPage(Adw.NavigationPage):
    """Page for selecting distribution family"""
    
    def __init__(self, main_window: Any) -> None:
        super().__init__()
        self.main_window = main_window
        self.set_title("Select Family")
        
        # Load family metadata
        self.families = self.load_families()
        
        # Create main content
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        content.set_margin_start(16)
        content.set_margin_end(16)
        
        # Title
        title = Gtk.Label(label="Choose Distribution Family")
        title.add_css_class("title-1")
        content.append(title)
        
        description = Gtk.Label(
            label="Select a family to see related distributions, or view all available options."
        )
        description.add_css_class("dim-label")
        description.set_wrap(True)
        description.set_justify(Gtk.Justification.CENTER)
        content.append(description)
        
        # Family cards in a scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # Use Clamp for better centering with max width
        clamp = Adw.Clamp()
        clamp.set_maximum_size(600)
        clamp.set_tightening_threshold(400)
        
        cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cards_box.set_halign(Gtk.Align.FILL)
        cards_box.set_valign(Gtk.Align.CENTER)
        
        # Create family cards in order
        families_ordered = sorted(
            self.families.items(),
            key=lambda x: x[1].get('sort_order', 99)
        )
        
        for family_id, family_data in families_ordered:
            card = self.create_family_card(family_id, family_data)
            cards_box.append(card)
        
        clamp.set_child(cards_box)
        scrolled.set_child(clamp)
        content.append(scrolled)
        
        # Custom ISO button
        custom_iso_btn = Gtk.Button(label="📁 Add Custom ISO Files")
        custom_iso_btn.connect("clicked", self.on_custom_iso_clicked)
        custom_iso_btn.add_css_class("pill")
        custom_iso_btn.set_halign(Gtk.Align.CENTER)
        custom_iso_btn.set_size_request(300, -1)
        content.append(custom_iso_btn)
        
        # "View All" button
        view_all_btn = Gtk.Button(label="📋 View All Distros")
        view_all_btn.connect("clicked", self.on_view_all_clicked)
        view_all_btn.add_css_class("pill")
        view_all_btn.add_css_class("suggested-action")
        view_all_btn.set_halign(Gtk.Align.CENTER)
        view_all_btn.set_size_request(300, -1)
        content.append(view_all_btn)
        
        self.set_child(content)
    
    def load_families(self) -> dict:
        """Load family metadata from JSON"""
        try:
            data_dir = Path(__file__).parent.parent / "data"
            families_file = data_dir / "families.json"
            
            if families_file.exists():
                with open(families_file, 'r') as f:
                    data = json.load(f)
                    return data.get('families', {})
            else:
                logger.warning(f"Families file not found: {families_file}")
                return self.get_default_families()
        except Exception as e:
            logger.error(f"Error loading families: {e}")
            return self.get_default_families()
    
    def get_default_families(self) -> dict:
        """Fallback family definitions using DistroFamily enum"""
        return {
            DistroFamily.ARCH.value: {
                "name": "Arch-based",
                "display_name": DistroFamily.ARCH.display_name,
                "description": "Rolling release with cutting-edge packages",
                "icon": "🏔️",
                "sort_order": 1
            },
            DistroFamily.DEBIAN.value: {
                "name": "Debian-based",
                "display_name": DistroFamily.DEBIAN.display_name,
                "description": "Stable and well-tested distributions",
                "icon": "🌀",
                "sort_order": 2
            },
            DistroFamily.FEDORA.value: {
                "name": "Fedora-based",
                "display_name": DistroFamily.FEDORA.display_name,
                "description": "Modern features with frequent updates",
                "icon": "🎩",
                "sort_order": 3
            }
        }
    
    def create_family_card(self, family_id: str, family_data: dict) -> Gtk.Button:
        """Create an actionable card for a family"""
        from luxusb.utils.distro_manager import get_distro_manager
        
        # Count distros in this family
        all_distros = get_distro_manager().get_all_distros()
        count = sum(1 for d in all_distros if hasattr(d, 'family') and d.family == family_id)
        
        # Create button that looks like a card
        button = Gtk.Button()
        button.add_css_class("card")
        button.connect("clicked", self.on_family_selected, family_id)
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Icon/Emoji
        icon_label = Gtk.Label(label=family_data.get('icon', '📦'))
        icon_label.add_css_class("title-3")
        box.append(icon_label)
        
        # Text content
        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        text_box.set_hexpand(True)
        text_box.set_halign(Gtk.Align.START)
        
        # Family name
        name_label = Gtk.Label(label=family_data.get('display_name', family_id.capitalize()))
        name_label.set_halign(Gtk.Align.START)
        name_label.add_css_class("title-4")
        text_box.append(name_label)
        
        # Description
        desc_label = Gtk.Label(label=family_data.get('description', ''))
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_wrap(True)
        desc_label.add_css_class("dim-label")
        desc_label.add_css_class("caption")
        text_box.append(desc_label)
        
        # Count
        count_label = Gtk.Label(label=f"{count} distro{'s' if count != 1 else ''} available")
        count_label.set_halign(Gtk.Align.START)
        count_label.add_css_class("dim-label")
        count_label.add_css_class("caption")
        text_box.append(count_label)
        
        box.append(text_box)
        
        # Arrow icon
        arrow = Gtk.Image.new_from_icon_name("go-next-symbolic")
        arrow.set_valign(Gtk.Align.CENTER)
        box.append(arrow)
        
        button.set_child(box)
        return button
    
    def on_family_selected(self, _button: Gtk.Button, family_id: str) -> None:
        """Handle family selection"""
        logger.info(f"Selected family: {family_id}")
        
        # Navigate to distro selection page with family filter
        self.main_window.navigate_to_distro_page(family_filter=family_id)
    
    def on_view_all_clicked(self, _button: Gtk.Button) -> None:
        """Handle 'View All' button click"""
        logger.info("Viewing all distros")
        
        # Navigate to distro selection page without family filter
        self.main_window.navigate_to_distro_page(family_filter=None)
    
    def on_custom_iso_clicked(self, _button: Gtk.Button) -> None:
        """Handle 'Custom ISO' button click"""
        logger.info("Custom ISO button clicked")
        
        # Navigate to custom ISO page
        from luxusb.gui.custom_iso_page import CustomISOPage
        
        custom_iso_page = CustomISOPage(self.main_window)
        
        nav_view = self.main_window.nav_view
        nav_view.push(custom_iso_page)
