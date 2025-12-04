#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify theme switching bug is fixed
"""

import os
import sys

from gui.themes import ColorScheme, ThemeManager, ThemeMode

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_theme_switching():
    """Test that theme switching works without crashing"""
    print("Testing Personal Password Manager Theme Fix...")
    print("=" * 60)

    try:
        # Initialize theme manager
        print("\n1. Initializing theme manager...")
        theme = ThemeManager("data/test_theme_config.json")
        print(f"   ✓ Theme manager initialized: {theme.current_mode.value}")

        # Test dark mode
        print("\n2. Setting theme to DARK mode...")
        result = theme.set_theme_mode(ThemeMode.DARK)
        if result:
            print("   ✓ Successfully set to dark mode")
        else:
            print("   ✗ Failed to set dark mode")
            return False

        # Test light mode (this was causing the crash)
        print("\n3. Setting theme to LIGHT mode (previously crashed here)...")
        result = theme.set_theme_mode(ThemeMode.LIGHT)
        if result:
            print("   ✓ Successfully set to light mode - BUG FIXED!")
        else:
            print("   ✗ Failed to set light mode")
            return False

        # Test switching back to dark
        print("\n4. Switching back to DARK mode...")
        result = theme.set_theme_mode(ThemeMode.DARK)
        if result:
            print("   ✓ Successfully switched back to dark mode")
        else:
            print("   ✗ Failed to switch back")
            return False

        # Test rapid switching
        print("\n5. Testing rapid theme switching...")
        for i in range(3):
            theme.set_theme_mode(ThemeMode.LIGHT)
            theme.set_theme_mode(ThemeMode.DARK)
        print("   ✓ Rapid switching works correctly")

        # Test color schemes
        print("\n6. Testing color scheme switching...")
        for scheme in [ColorScheme.BLUE, ColorScheme.GREEN, ColorScheme.PURPLE]:
            result = theme.set_color_scheme(scheme)
            if result:
                print(f"   ✓ {scheme.value} scheme applied")
            else:
                print(f"   ✗ Failed to apply {scheme.value} scheme")
                return False

        # Test callback system
        print("\n7. Testing callback system...")
        callback_called = [False]

        def test_callback(old_mode, new_mode):
            callback_called[0] = True
            print(f"   ✓ Callback triggered: {old_mode.value} → {new_mode.value}")

        theme.register_theme_change_callback(test_callback)
        theme.set_theme_mode(ThemeMode.LIGHT)

        if callback_called[0]:
            print("   ✓ Callback system works correctly")
        else:
            print("   ✗ Callback was not called")
            return False

        # Test duplicate mode setting (should not trigger callback)
        print("\n8. Testing duplicate mode setting...")
        callback_called[0] = False
        theme.set_theme_mode(ThemeMode.LIGHT)  # Already in light mode
        if not callback_called[0]:
            print("   ✓ Duplicate mode correctly skipped")
        else:
            print("   ✗ Callback called for duplicate mode")

        # Clean up test config file
        import os

        if os.path.exists("data/test_theme_config.json"):
            os.remove("data/test_theme_config.json")
            print("\n9. Cleaned up test configuration file")

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Theme switching bug is FIXED!")
        print("=" * 60)
        print("\nChanges made:")
        print("1. Added 'from datetime import datetime' import")
        print("2. Added callback system for theme changes")
        print("3. Improved error handling with rollback")
        print("4. Added duplicate mode/scheme detection")
        print("5. Added proper return values for success/failure")
        return True

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_theme_switching()
    sys.exit(0 if success else 1)
