# AppImage build (manual)

1. Build wheel: `python -m build`
2. Create AppDir with `linuxdeploy` or `appimagetool`
3. Bundle PySide6 Qt libraries into `usr/lib`
4. Copy `packaging/knightpac.desktop` and icons into AppDir
5. Run `appimagetool KnightPac.AppDir KnightPac-x86_64.AppImage`

Not automated in this repository.
