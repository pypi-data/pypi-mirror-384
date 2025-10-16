"""
Entry point for RC3 Command Center
Run with: rc3
"""

from rc3.core.app import RC3App


def main():
    """Launch the RC3 Command Center"""
    app = RC3App()
    app.run()


if __name__ == "__main__":
    main()


