__all__ = ['deep_get']

def deep_get(data, target_path, default=None):
    """
    중첩된 데이터 구조에서 경로와 일치하는 첫 번째 값을 재귀적으로 찾습니다.

    예를 들어, target_path가 'a/b'이면 데이터 내의 어느 깊이에서든
    {'a': {'b': value}} 구조를 찾아 value를 반환합니다.
    단일 키 'a'는 길이가 1인 경로로 취급됩니다.

    :param data: 검색할 데이터 구조입니다.
    :param target_path: 찾을 키 또는 슬래시('/')로 구분된 경로입니다.
    :param default: 값을 찾지 못했을 때 반환할 기본값입니다.
    """
    path_keys = target_path.split('/')

    def _search(current_data):
        # 1단계: 현재 위치(current_data)에서 경로가 시작되는지 확인
        temp = current_data
        try:
            for key in path_keys:
                temp = temp[key]
            # 예외 없이 모든 경로를 통과했다면 값을 찾은 것이므로 즉시 반환
            return temp
        except (KeyError, TypeError, IndexError):
            # 현재 위치에서는 경로가 시작되지 않음. 계속해서 더 깊이 탐색.
            pass

        # 2단계: 현재 위치에서 경로를 못 찾았다면, 하위 요소들을 재귀적으로 탐색
        if isinstance(current_data, dict):
            for value in current_data.values():
                found = _search(value)
                if found is not None:
                    return found
        elif isinstance(current_data, list):
            for item in current_data:
                found = _search(item)
                if found is not None:
                    return found

        # 모든 탐색을 마쳤지만 현재 경로에서 값을 찾지 못함
        return None

    result = _search(data)

    return result if result is not None else default