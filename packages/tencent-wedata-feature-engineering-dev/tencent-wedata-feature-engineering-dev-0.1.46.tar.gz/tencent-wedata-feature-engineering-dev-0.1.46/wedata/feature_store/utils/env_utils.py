import os


class EnvironmentError(Exception):
    pass


def get_project_id() -> str:
    """
    获取当前项目名称
    
    Returns:
        str: 项目ID
        
    Raises:
        ValueError: 当环境变量 WEDATA_PROJECT_ID 未设置时
    """
    project_id = os.environ.get("WEDATA_PROJECT_ID")
    if project_id:
        return project_id
    raise EnvironmentError("environment variable WEDATA_PROJECT_ID is not set, please check environment configuration")


def get_cloud_secret() -> (str, str):
    """
    获取云上密钥

    Returns:
        tuple: 包含云上密钥的元组
    """
    secret_id = os.environ.get("WEDATA_CLOUD_TEMP_SECRET_ID")
    secret_key = os.environ.get("WEDATA_CLOUD_TEMP_SECRET_KEY")
    return secret_id, secret_key


def get_region() -> str:
    """
    获取当前地域
    """
    region_dlc = os.environ.get("DLC_REGION")
    region_emr = os.environ.get("KERNEL_REGION")
    region = region_dlc if region_dlc else region_emr
    if not region:
        raise EnvironmentError("environment variable DLC_REGION or KERNEL_REGION is not set, "
                               "please check environment configuration")
    return region


def get_database_name(database_name: str) -> str:
    """
    获取数据库名称

    Args:
        database_name: 数据库名称

    Returns:
        str: 数据库名称

    Raises:
        EnvironmentError: 当环境变量 WEDATA_DEFAULT_FEATURE_STORE_DATABASE 未设置时
    """
    feature_store_database_name = os.environ.get("WEDATA_DEFAULT_FEATURE_STORE_DATABASE")
    if database_name:
        return database_name
    elif feature_store_database_name:
        return feature_store_database_name
    raise EnvironmentError("environment variable WEDATA_DEFAULT_FEATURE_STORE_DATABASE is not set, "
                           "please check environment configuration")


def get_engine_name() -> str:
    """
    获取引擎名称
    """
    return _get_variable("KERNEL_ENGINE_NAME")


def get_engine_id() -> str:
    """
    获取引擎ID
    """
    return _get_variable("KERNEL_ENGINE")


def get_engine_type() -> str:
    """
    判断引擎类型
    """
    return "DLC" if os.environ.get("DLC_REGION") else "EMR"


def get_feast_remote_url() -> str:
    """
    获取Feast远程URL
    """
    return _get_variable("KERNEL_FEAST_REMOTE_ADDRESS")


def _get_variable(variable_key: str, is_raise: bool = True, default_value: str = None) -> str:
    val = os.environ.get(variable_key, default_value)
    if not val:
        if is_raise:
            raise EnvironmentError(f"environment variable {variable_key} is not set, "
                                   f"please check environment configuration")
    return val
