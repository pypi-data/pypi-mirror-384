def replace_specific_punctuation(
    input_string=r"SMT10線A001 DS01G機種B/C批性漏扫描(TS站未扫描显示ASG))之異常！))",
    punctuation_string=r"/,=,！, (,),("
):
    """
    将输入字符串中指定的标点符号替换为空格。
    Replace specific punctuation marks in the input string with spaces.

    Args:
        input_string (str, optional):
            需要进行标点符号替换的字符串。
            The input string where punctuation marks need to be replaced.
            默认为 "SMT10線A001 DS01G機種B/C批性漏扫描(TS站未扫描显示ASG))之異常！))"。
            Defaults to "SMT10線A001 DS01G機種B/C批性漏扫描(TS站未扫描显示ASG))之異常！))".

        punctuation_string (str, optional):
            包含需要替换的标点符号的字符串，
            A string containing the punctuation marks to be replaced,
            标点符号之间用逗号分隔。
            with punctuation marks separated by commas.
            默认为 "/,=,！, (,),("。
            Defaults to "/,=,！, (,),(".

    Returns:
        str: 替换掉指定标点符号后的字符串。
        str: The string with the specified punctuation marks replaced by spaces.
    """
    # 将包含标点符号的字符串分割成列表
    # Split the string containing punctuation marks into a list.
    punctuation_list = punctuation_string.split(",")

    # 遍历标点符号列表，将每个标点符号替换为空格
    # Iterate through the list of punctuation marks and replace each one with a space.
    for punctuation_mark in punctuation_list:
        input_string = input_string.replace(punctuation_mark, " ")

    # 返回替换后的字符串
    # Return the string after the replacements.
    return input_string


# 调用函数并获取替换后的结果
# Call the function and get the result after replacement.
result = replace_specific_punctuation()

# 打印替换后的结果
# Print the result after replacement.
#print(result)