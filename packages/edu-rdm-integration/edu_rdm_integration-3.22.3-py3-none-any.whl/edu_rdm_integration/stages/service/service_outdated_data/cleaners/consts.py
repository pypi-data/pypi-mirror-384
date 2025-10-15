from web_edu.plugins.regional_data_mart_integration.models.homework import Homework
from web_edu.plugins.regional_data_mart_integration.models.homework_material import HomeworkMaterial
from web_edu.plugins.regional_data_mart_integration.models.homework_student import HomeworkStudent


UNION_CHUNK_SIZE = 5

OLD_RDM_MODEL = [
    HomeworkStudent,
    HomeworkMaterial,
    Homework,
]