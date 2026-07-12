{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  buildInputs = [
    pkgs.python313
    pkgs.python313Packages.pip
    pkgs.python313Packages.virtualenv
    pkgs.python313Packages.tkinter
    pkgs.linuxHeaders
    pkgs.gcc
    pkgs.zenity
    pkgs.stdenv.cc.cc.lib

    pkgs.qt5.qtbase
    pkgs.libGL
    pkgs.fontconfig
    pkgs.freetype
    pkgs.xorg.libX11
    pkgs.xorg.libxcb
    pkgs.xorg.libXrandr
    pkgs.xorg.libXi
    pkgs.xorg.libXext
    pkgs.xorg.libXfixes
    pkgs.xorg.libXrender
    pkgs.xorg.libSM
    pkgs.xorg.libICE
    pkgs.glib
    pkgs.libxkbcommon
    pkgs.dbus
    pkgs.nspr
    pkgs.nss

    pkgs.xorg.xcbutil
    pkgs.xorg.xcbutilcursor
    pkgs.xorg.xcbutilimage
    pkgs.xorg.xcbutilkeysyms
    pkgs.xorg.xcbutilrenderutil
    pkgs.xorg.xcbutilwm
  ];

  C_INCLUDE_PATH = "${pkgs.linuxHeaders}/include";

  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib
    pkgs.libGL
    pkgs.fontconfig
    pkgs.freetype
    pkgs.xorg.libX11
    pkgs.xorg.libxcb
    pkgs.xorg.libXrandr
    pkgs.xorg.libXi
    pkgs.xorg.libXext
    pkgs.xorg.libXfixes
    pkgs.xorg.libXrender
    pkgs.xorg.libSM
    pkgs.xorg.libICE
    pkgs.glib
    pkgs.libxkbcommon
    pkgs.dbus
    pkgs.nspr
    pkgs.nss

    pkgs.xorg.xcbutil
    pkgs.xorg.xcbutilcursor
    pkgs.xorg.xcbutilimage
    pkgs.xorg.xcbutilkeysyms
    pkgs.xorg.xcbutilrenderutil
    pkgs.xorg.xcbutilwm
  ];

  shellHook = ''
    source venv/bin/activate
  '';
}
