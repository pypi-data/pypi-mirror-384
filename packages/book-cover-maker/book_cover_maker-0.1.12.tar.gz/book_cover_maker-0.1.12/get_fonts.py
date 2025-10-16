import sys
import os
import shutil
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("사용법: python gen_cover.py <폰트이름키워드> <대상폴더>")
        sys.exit(1)

    keyword = sys.argv[1].lower()
    dest_folder = Path(sys.argv[2])
    dest_folder.mkdir(parents=True, exist_ok=True)

    # Windows 시스템 폰트 폴더
    font_dirs = [
        Path("C:/Windows/Fonts"),
        Path.home() / "AppData/Local/Microsoft/Windows/Fonts"
    ]

    found_fonts = []

    for font_dir in font_dirs:
        if not font_dir.exists():
            continue
        for font_file in font_dir.glob("*.*"):
            if keyword in font_file.name.lower() and font_file.suffix.lower() in [".ttf", ".otf"]:
                found_fonts.append(font_file)

    if not found_fonts:
        print(f"'{keyword}' 이 포함된 폰트를 찾을 수 없습니다.")
        return

    print(f"{len(found_fonts)}개의 폰트를 복사합니다...")

    for font_file in found_fonts:
        target = dest_folder / font_file.name
        shutil.copy2(font_file, target)
        print(f"복사 완료: {font_file.name}")

    print(f"\n✅ 모든 폰트가 '{dest_folder}' 폴더로 복사되었습니다.")

if __name__ == "__main__":
    main()
