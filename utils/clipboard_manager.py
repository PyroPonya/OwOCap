"""
Менеджер буфера обмена для Windows (utils/clipboard_manager.py)
Использует pywin32 для максимальной производительности и поддержки изображений.
"""

import io
from typing import Optional, Union
from PIL import Image
import numpy as np
# как использовать:
# from utils.clipboard_manager import get_clipboard
# class ScreenshotService:
#     def __init__(self):
# Используем глобальный экземпляр
#         self.clipboard = get_clipboard()
#     def save_screenshot(self, image):
#         """Сохраняет скриншот в буфер обмена"""
#         success = self.clipboard.save_image(image)
#         if success:
#             print("Скриншот сохранен в буфер обмена Windows")
#         return success


class ClipboardManager:
    """
    Оптимизированный менеджер буфера обмена для Windows.

    Особенности:
    1. Приоритетное использование pywin32 для работы с изображениями
    2. Pyperclip для текстовых операций
    3. Поддержка numpy 2.x через проверку версий
    4. Единый интерфейс для текста и изображений
    """

    def __init__(self):
        """Инициализация с проверкой доступных библиотек"""
        self._has_win32 = False
        self._has_pyperclip = False
        self._has_tkinter = False

        # Проверяем и импортируем pywin32
        try:
            import win32clipboard
            self.win32clipboard = win32clipboard
            self._has_win32 = True
        except ImportError as e:
            print(
                f"Внимание: pywin32 не доступен. Изображения не будут копироваться. Ошибка: {e}")

        # Проверяем и импортируем pyperclip
        try:
            import pyperclip
            self.pyperclip = pyperclip
            self._has_pyperclip = True
        except ImportError:
            print(
                "Внимание: pyperclip не доступен. Будет использован tkinter для текста.")

        # Инициализируем tkinter как резервный вариант
        try:
            import tkinter as tk
            self.tk = tk
            self._tk_root = tk.Tk()
            self._tk_root.withdraw()  # Скрываем окно
            self._has_tkinter = True
        except Exception as e:
            print(f"Внимание: не удалось инициализировать tkinter: {e}")
            self._tk_root = None

    # ----------------------------------------------------------------
    # ОСНОВНОЙ ПУБЛИЧНЫЙ ИНТЕРФЕЙС
    # ----------------------------------------------------------------

    def save_text(self, text: str) -> bool:
        """
        Сохраняет текст в буфер обмена Windows.

        Args:
            text (str): Текст для сохранения

        Returns:
            bool: True если успешно, False в случае ошибки

        Пример:
            >>> clipboard.save_text("Привет, Windows!")
            True
        """
        if not isinstance(text, str):
            print(f"Ошибка: ожидалась строка, получен {type(text)}")
            return False

        try:
            # Приоритет 1: Pyperclip (быстрее и надежнее для текста)
            if self._has_pyperclip:
                self.pyperclip.copy(text)
                return True

            # Приоритет 2: Pywin32 (Windows native)
            if self._has_win32:
                self.win32clipboard.OpenClipboard()
                self.win32clipboard.EmptyClipboard()
                self.win32clipboard.SetClipboardText(text)
                self.win32clipboard.CloseClipboard()
                return True

            # Приоритет 3: Tkinter (резерв)
            if self._has_tkinter:
                self._tk_root.clipboard_clear()
                self._tk_root.clipboard_append(text)
                self._tk_root.update()  # Фиксируем изменения
                return True

            print("Ошибка: нет доступных методов для работы с буфером обмена")
            return False

        except Exception as e:
            print(f"Критическая ошибка при сохранении текста: {e}")
            return False

    def save_image(self, image_data: Union[Image.Image, bytes, np.ndarray, str]) -> bool:
        """
        Сохраняет изображение в буфер обмена Windows.

        Args:
            image_data: Данные изображения в одном из форматов:
                       - PIL.Image.Image
                       - bytes (PNG/BMP/JPEG)
                       - numpy.ndarray (HxWxC или HxW)
                       - str (путь к файлу)

        Returns:
            bool: True если успешно, False в случае ошибки

        Примеры:
            >>> # Из PIL Image
            >>> img = Image.open("screenshot.png")
            >>> clipboard.save_image(img)

            >>> # Из numpy array (совместимость с вашим numpy 2.3.5)
            >>> array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            >>> clipboard.save_image(array)

            >>> # Из файла
            >>> clipboard.save_image("C:/path/to/image.png")
        """
        try:
            # Конвертируем в PIL Image
            pil_image = self._convert_to_pil(image_data)
            if pil_image is None:
                return False

            # Используем Windows-специфичный метод
            return self._save_image_windows(pil_image)

        except Exception as e:
            print(f"Ошибка при сохранении изображения: {e}")
            return False

    # ----------------------------------------------------------------
    # ПРИВАТНЫЕ МЕТОДЫ ДЛЯ РАБОТЫ С ИЗОБРАЖЕНИЯМИ
    # ----------------------------------------------------------------

    def _convert_to_pil(self, image_data) -> Optional[Image.Image]:
        """Конвертирует различные форматы в PIL Image"""
        try:
            # Если уже PIL Image
            if isinstance(image_data, Image.Image):
                return image_data

            # Если путь к файлу (строка)
            elif isinstance(image_data, str):
                return Image.open(image_data)

            # Если bytes
            elif isinstance(image_data, bytes):
                return Image.open(io.BytesIO(image_data))

            # Если numpy array (совместимость с numpy 2.3.5)
            elif isinstance(image_data, np.ndarray):
                # Проверяем версию numpy для совместимости
                np_version = tuple(map(int, np.__version__.split('.')[:2]))

                if np_version >= (2, 0):
                    # numpy 2.x - используем стандартный метод
                    return Image.fromarray(image_data)
                else:
                    # numpy 1.x - проверяем типы данных
                    if image_data.dtype == np.uint8:
                        return Image.fromarray(image_data)
                    else:
                        # Конвертируем в uint8 если нужно
                        normalized = np.clip(
                            image_data, 0, 255).astype(np.uint8)
                        return Image.fromarray(normalized)

            else:
                print(f"Неподдерживаемый формат: {type(image_data)}")
                return None

        except Exception as e:
            print(f"Ошибка конвертации в PIL: {e}")
            return None

    def _save_image_windows(self, image: Image.Image) -> bool:
        """
        Основной метод сохранения изображения через Windows API.
        Использует формат DIB (Device Independent Bitmap).
        """
        if not self._has_win32:
            print("Ошибка: pywin32 недоступен для сохранения изображений")
            return False

        try:
            # Конвертируем в режим RGB если нужно
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Создаем BMP в памяти (Windows ожидает именно BMP для буфера обмена)
            output = io.BytesIO()

            # Сохраняем как BMP
            # Важно: не использовать сжатие
            image.save(output, 'BMP', compress_level=0)
            bmp_data = output.getvalue()
            output.close()

            # Windows требует DIB формат (BMP без заголовка файла)
            # Заголовок BMP файла = 14 байт
            dib_data = bmp_data[14:]

            # Копируем в буфер обмена Windows
            self.win32clipboard.OpenClipboard()
            self.win32clipboard.EmptyClipboard()

            # Используем CF_DIB для совместимости
            self.win32clipboard.SetClipboardData(
                self.win32clipboard.CF_DIB,
                dib_data
            )

            self.win32clipboard.CloseClipboard()
            return True

        except Exception as e:
            print(f"Ошибка Windows API при сохранении изображения: {e}")

            # Пробуем закрыть буфер обмена если произошла ошибка
            try:
                self.win32clipboard.CloseClipboard()
            except:
                pass

            return False

    # ----------------------------------------------------------------
    # ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ
    # ----------------------------------------------------------------

    def get_text(self) -> Optional[str]:
        """
        Получает текст из буфера обмена Windows.

        Returns:
            str или None если буфер пуст или произошла ошибка
        """
        try:
            # Приоритет 1: Pyperclip
            if self._has_pyperclip:
                return self.pyperclip.paste()

            # Приоритет 2: Windows API
            if self._has_win32:
                self.win32clipboard.OpenClipboard()
                try:
                    # Пробуем получить текст
                    if self.win32clipboard.IsClipboardFormatAvailable(
                        self.win32clipboard.CF_UNICODETEXT
                    ):
                        data = self.win32clipboard.GetClipboardData(
                            self.win32clipboard.CF_UNICODETEXT
                        )
                        return str(data) if data else None
                finally:
                    self.win32clipboard.CloseClipboard()

            # Приоритет 3: Tkinter
            if self._has_tkinter:
                try:
                    return self._tk_root.clipboard_get()
                except:
                    return None

            return None

        except Exception as e:
            print(f"Ошибка при получении текста: {e}")
            return None

    def clear(self) -> bool:
        """Очищает буфер обмена Windows"""
        try:
            # Приоритет: Windows API
            if self._has_win32:
                self.win32clipboard.OpenClipboard()
                self.win32clipboard.EmptyClipboard()
                self.win32clipboard.CloseClipboard()
                return True

            # Альтернатива: пустой текст
            return self.save_text("")

        except Exception as e:
            print(f"Ошибка при очистке буфера: {e}")
            return False

    # ----------------------------------------------------------------
    # УТИЛИТЫ И КОНТЕКСТНЫЕ МЕНЕДЖЕРЫ
    # ----------------------------------------------------------------

    def __enter__(self):
        """Поддержка контекстного менеджера"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Очистка ресурсов при выходе из контекста"""
        self.close()

    def close(self):
        """Освобождение ресурсов (особенно tkinter)"""
        if hasattr(self, '_tk_root') and self._tk_root:
            try:
                self._tk_root.destroy()
            except:
                pass

    def __del__(self):
        """Деструктор - автоматическая очистка"""
        self.close()

# ----------------------------------------------------------------
# ГЛОБАЛЬНЫЙ СИНГЛТОН И УДОБНЫЕ ФУНКЦИИ
# ----------------------------------------------------------------


_clipboard_instance = None


def get_clipboard() -> ClipboardManager:
    """
    Возвращает глобальный экземпляр менеджера буфера обмена.

    Returns:
        ClipboardManager: Единый экземпляр для всего приложения

    Пример:
        >>> from utils.clipboard_manager import get_clipboard
        >>> clipboard = get_clipboard()
        >>> clipboard.save_text("Пример")
    """
    global _clipboard_instance
    if _clipboard_instance is None:
        _clipboard_instance = ClipboardManager()
    return _clipboard_instance

# Удобные функции для быстрого доступа


def copy_text(text: str) -> bool:
    """Быстрое копирование текста в буфер обмена"""
    return get_clipboard().save_text(text)


def copy_image(image_data) -> bool:
    """Быстрое копирование изображения в буфер обмена"""
    return get_clipboard().save_image(image_data)


def paste_text() -> Optional[str]:
    """Быстрое получение текста из буфера обмена"""
    return get_clipboard().get_text()


def clear_clipboard() -> bool:
    """Быстрая очистка буфера обмена"""
    return get_clipboard().clear()

# ----------------------------------------------------------------
# ТЕСТИРОВАНИЕ И ДЕМОНСТРАЦИЯ
# ----------------------------------------------------------------


if __name__ == "__main__":
    """
    Тестирование функционала менеджера буфера обмена.
    Запустите этот файл для проверки работоспособности.
    """
    print("=" * 60)
    print("Тестирование ClipboardManager для Windows")
    print("=" * 60)

    # Создаем экземпляр
    cm = ClipboardManager()

    # Тест 1: Текст
    print("\n1. Тестирование работы с текстом...")
    test_text = "Тестовый текст из ClipboardManager 🚀"

    if cm.save_text(test_text):
        print(f"   ✓ Текст скопирован: '{test_text}'")

        retrieved = cm.get_text()
        if retrieved == test_text:
            print(f"   ✓ Текст получен корректно: '{retrieved}'")
        else:
            print(f"   ✗ Ошибка: получен '{retrieved}'")
    else:
        print("   ✗ Ошибка копирования текста")

    # Тест 2: Изображение (создаем тестовое)
    print("\n2. Тестирование работы с изображениями...")

    try:
        # Создаем простое тестовое изображение
        img = Image.new('RGB', (200, 100), color='blue')

        # Добавляем текст на изображение
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        draw.text((20, 40), "Windows Clipboard Test", fill='white', font=font)

        # Копируем в буфер обмена
        if cm.save_image(img):
            print("   ✓ Изображение успешно скопировано в буфер обмена")
            print("   Проверьте: откройте Paint и нажмите Ctrl+V")
        else:
            print("   ✗ Ошибка копирования изображения")

    except Exception as e:
        print(f"   ✗ Ошибка при создании тестового изображения: {e}")
