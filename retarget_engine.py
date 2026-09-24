import os
import sys
import subprocess
import shutil

class RetargetEngine:
    def __init__(self, mapping_path):
        self.mapping_path = os.path.abspath(mapping_path)
        self.blender_executable = self.find_blender()

    def find_blender(self):
        """
        Автоматический поиск установленного Blender на Windows / Mac / Linux
        """
        # 1. Проверяем PATH
        b = shutil.which("blender")
        if b:
            return b

        # 2. Стандартные пути на Windows
        win_paths = [
            r"C:\Program Files\Blender Foundation\Blender 4.3\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.4\blender.exe",
            r"C:\Program Files\Blender Foundation\Blender 3.3\blender.exe",
            r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
            r"D:\Steam\steamapps\common\Blender\blender.exe",
            r"D:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
            r"D:\Program Files\Blender Foundation\Blender 4.1\blender.exe",
            r"D:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
        ]
        for p in win_paths:
            if os.path.exists(p):
                return p

        # 3. Стандартные пути на macOS
        mac_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/Applications/Blender 4.2.app/Contents/MacOS/Blender",
            "/Applications/Blender 4.1.app/Contents/MacOS/Blender",
            "/Applications/Blender 4.0.app/Contents/MacOS/Blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender")
        ]
        for p in mac_paths:
            if os.path.exists(p):
                return p

        return None

    def process_file(self, src_fbx_path, target_rig_path, output_fbx_path, progress_callback=None):
        if not self.blender_executable or not os.path.exists(self.blender_executable):
            raise RuntimeError(
                "Blender не найден на компьютере!\n\n"
                "Для точного ретаргета и экспорта FBX нужен установленный Blender (v3.6+).\n"
                "Установите Blender или добавьте путь к blender.exe."
            )

        src_fbx = os.path.abspath(src_fbx_path)
        target_rig = os.path.abspath(target_rig_path)
        out_fbx = os.path.abspath(output_fbx_path)
        
        # Получаем абсолютный путь к worker скрипту рядом с текущим файлом
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(cur_dir, "blender_retarget_worker.py")

        if progress_callback:
            progress_callback(0.2, "Запуск фонового ретаргета в Blender...")

        cmd = [
            self.blender_executable,
            "-b",
            "--factory-startup",
            "-P", script,
            "--",
            src_fbx,
            target_rig,
            out_fbx,
            self.mapping_path
        ]

        if progress_callback:
            progress_callback(0.5, "Запекание костей и анимации...")

        res = subprocess.run(cmd, capture_output=True, text=True)

        if res.returncode != 0:
            print("BLENDER ERROR OUTPUT:\n", res.stderr or res.stdout)
            raise RuntimeError(f"Ошибка при обработке в Blender:\n{res.stderr or res.stdout}")

        if not os.path.exists(out_fbx):
            raise RuntimeError(f"Файл не был создан. Лог Blender:\n{res.stdout}")

        if progress_callback:
            progress_callback(1.0, "Готово!")

        return True
