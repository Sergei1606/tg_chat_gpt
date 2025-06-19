import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Путь к папке с изображениями
IMAGE_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'images')


def get_image(image_name: str) -> Optional[str]:
    """
    Возвращает путь к изображению по его названию.

    Args:
        image_name: Название изображения (без расширения)

    Returns:
        Полный путь к файлу изображения или None, если файл не найден
    """
    try:
        # Поддерживаемые форматы изображений
        supported_formats = ['.jpg', '.jpeg', '.png']

        # Проверяем все форматы
        for ext in supported_formats:
            image_path = os.path.join(IMAGE_FOLDER, f"{image_name}{ext}")
            if os.path.exists(image_path):
                return image_path

        logger.warning(f"Image not found: {image_name}")
        return None

    except Exception as e:
        logger.error(f"Error in get_image: {e}")
        return None