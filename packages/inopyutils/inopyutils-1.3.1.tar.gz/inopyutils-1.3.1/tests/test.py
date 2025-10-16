import asyncio
from pathlib import Path

from src.inopyutils import InoFileHelper, InoLogHelper, InoMediaHelper

from src.inopyutils import SparkHelper

async def test_validate_files():
    result = await InoFileHelper.validate_files(
        input_path=Path(r"E:\NIL\spark\python\InoFacefusion\.jobs2\3"),
        include_image=True,
        include_video=False
    )
    print(result)

async def test_spark_helper():
    spark_helper = SparkHelper()

async def test_log_helper():
    log_helper = InoLogHelper(
        path_to_save=Path(r"E:\NIL\spark\python\InoFacefusion\.logs\UploadWorker"),
        log_name="UploadWorker")
    test_log = {
        "msg": "Hello World!"
    }
    log_helper.add_log(test_log)
    return None

async def test_image_validate():
    validate_image = await InoMediaHelper.image_validate_pillow(
        input_path=Path(r"E:\NIL\spark\python\InoGenie\assets\Karla\Face_Swap_Normal_Batch\Batch_00004\IMG_1644.jpeg"),
        output_path=Path(r"E:\NIL\spark\python\InoGenie\assets\Karla\Face_Swap_Normal_Batch\Batch_00004\Karla_999.jpg"),
        max_res=2048
    )
    print(validate_image)

if __name__ == "__main__":
    asyncio.run(test_image_validate())
