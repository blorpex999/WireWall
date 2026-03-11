from __future__ import annotations

from pathlib import Path


def main() -> int:
    version = Path("VERSION").read_text(encoding="utf-8").strip()
    parts = version.split(".")
    while len(parts) < 4:
        parts.append("0")
    version_tuple = ", ".join(parts[:4])

    target = Path("build") / "version_info.txt"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_tuple}),
    prodvers=({version_tuple}),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040C04B0',
        [
          StringStruct('CompanyName', 'Ynov Campus'),
          StringStruct('FileDescription', 'WireWall - Surveillance USB Windows'),
          StringStruct('FileVersion', '{version}'),
          StringStruct('InternalName', 'WireWall'),
          StringStruct('OriginalFilename', 'WireWall.exe'),
          StringStruct('ProductName', 'WireWall'),
          StringStruct('ProductVersion', '{version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1036, 1200])])
  ]
)
""",
        encoding="utf-8",
    )
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
