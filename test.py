import re
result = "[[ID10, ID11], [ID12, ID13], [ID15, ID17], [ID24, ID25], [ID28, ID29], [ID31, ID36], [ID63, ID64], [ID72, ID73], [ID76, ID78], [ID85, ID86], [ID88, ID91]]"
try:
    if result.strip() == "[]":
        duplicate_groups = []
    else:
        # 尝试直接解析为Python列表
        try:
            parsed_groups = eval(result.strip())
            duplicate_groups = []
            for group in parsed_groups:
                if isinstance(group, list) and len(group) >= 2:
                    # 将数字转换为ID格式
                    id_group = [f"ID{num}" for num in group if isinstance(num, int)]
                    if len(id_group) >= 2:
                        duplicate_groups.append(id_group)
        except:
            # 如果eval失败，使用正则表达式提取数字组合
            pattern = r'\[([0-9,\s]+)\]'
            matches = re.findall(pattern, result)
            print(f"  📊 AI返回结果: {matches}")
            duplicate_groups = []
            for match in matches:
                # 提取数字并转换为ID
                numbers = re.findall(r'\d+', match)
                if len(numbers) >= 2:
                    ids = [f"ID{num}" for num in numbers]
                    duplicate_groups.append(ids)
                
except Exception as e:
    print(f"  ⚠️ 解析AI返回结果失败: {e}")
    duplicate_groups = []

if not duplicate_groups:
    print("  📊 AI未发现重复文章")
    