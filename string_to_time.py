class StringToTime:
    #Can either be instantiated with the desired return type and format or used directly
    #If instantiated, use translate, if not, use convert
    def __init__(self, input_unit="ms", input_format=0, return_unit="ms", return_type="int", return_format=1):
        self.return_unit = return_unit
        self.input_format = input_format
        self.return_type = return_type
        self.input_unit = input_unit
        self.return_format = return_format
    
    def translate(self, input):
        num = 0
        num_str = ""
        input = input.replace(" ", "")
        input = input.lower()
        format = 0

        #Automatically select format
        if self.input_format == 0:
            for i in input:
                if i.isalpha():
                    format = 1
                    break
                else:
                    format = 2

        #Match format instead of self because of auto detection
        match format:
            case 1: #__h __m __s ___ or __h__m__s___
                for idx, i in enumerate(input):
                    if i.isdigit():
                        num_str += i
                    elif num_str != "":
                        match i:
                            case "h":
                                num += int(num_str) * 3600000
                            case "m":
                                if len(input) > idx + 1:
                                    if input[idx + 1] != "s":
                                        num += int(num_str) * 60000
                                    else:
                                        num += int(num_str)
                                else:
                                    num += int(num_str) * 60000
                            case "s":
                                num += int(num_str) * 1000
                            case _:
                                num += int(num_str)
                        num_str = ""
                #If last char is a digit, assume it's in ms
                if num_str != "":
                    num += int(num_str)
                        
            case 2: #__:__:__.___
                div_num = 0
                for i in input:
                    if not i.isdigit():
                        div_num += 1
                for i in input:
                    if i.isdigit():
                        num_str += i
                    else:
                    #elif num_str != "":
                        match div_num:
                            case 3:
                                num += int(num_str) * 3600000
                                div_num -= 1
                                num_str = ""
                            case 2:
                                num += int(num_str) * 60000
                                div_num -= 1
                                num_str = ""
                            case 1:
                                num += int(num_str) * 1000
                                div_num -= 1
                                num_str = ""
                if num_str != "":
                    num += int(num_str)

        match self.return_unit.casefold():
            case "ms":
                return num
            case "s":
                return num // 1000 if self.return_type == "int" else num / 1000
            case "m":
                return num // 60000 if self.return_type == "int" else num / 60000
            case "h":
                return num // 3600000 if self.return_type == "int" else num / 3600000

    def convert(input, return_unit="ms", input_format=0, return_type = "int"):
        num = 0
        num_str = ""
        input = input.replace(" ", "")
        input = input.lower()

        #Automatically select format
        if input_format == 0:
            for i in input:
                if i.isalpha():
                    format = 1
                    break
                else:
                    format = 2

        match input_format:
            case 1: #__h __m __s ___ or __h__m__s___
                for idx, i in enumerate(input):
                    if i.isdigit():
                        num_str += i
                    elif num_str != "":
                        match i.casefold():
                            case "h":
                                num += int(num_str) * 3600000
                            case "m":
                                if len(input) > idx + 1:
                                    if input[idx + 1] != "s":
                                        num += int(num_str) * 60000
                                    else:
                                        num += int(num_str)
                                else:
                                    num += int(num_str) * 60000
                            case "s":
                                num += int(num_str) * 1000
                            case _:
                                num += int(num_str)
                        num_str = ""
                #If last char is a digit, assume it's in ms
                if num_str != "":
                    num += int(num_str)
                        
            case 2: #__:__:__.___
                div_num = 0
                for i in input:
                    if not i.isdigit():
                        div_num += 1
                for i in input:
                    if i.isdigit():
                        num_str += i
                    else:
                    #elif num_str != "":
                        match div_num:
                            case 3:
                                num += int(num_str) * 3600000
                                div_num -= 1
                                num_str = ""
                            case 2:
                                num += int(num_str) * 60000
                                div_num -= 1
                                num_str = ""
                            case 1:
                                num += int(num_str) * 1000
                                div_num -= 1
                                num_str = ""
                if num_str != "":
                    num += int(num_str)

        match return_unit.casefold():
            case "ms":
                return num
            case "s":
                return num // 1000 if return_type == "int" else num / 1000
            case "m":
                return num // 60000 if return_type == "int" else num / 60000
            case "h":
                return num // 3600000 if return_type == "int" else num / 3600000
    
    def convertTimeToString(num, input_unit="ms", return_format=1):
        output = ""
        match input_unit:
            case "ms":
                pass
            case "s":
                num *= 1000
            case "m":
                num *= 60000
            case "_":
                raise Exception("Invalid input type [ms/s/m]")
        num = int(num)
        match return_format:
            case 1 | 3:
                #Hours
                val = num // 3600000
                if val > 0:
                    output += str(val) + "h "
                    num %= 3600000
                #Minutes
                val = num // 60000
                if val > 0:
                    output += str(val) + "m "
                    num %= 60000
                #Seconds
                val = num // 1000
                if val > 0:
                    output += str(val) + "s "
                    num %= 1000
                #Milliseconds
                if num > 0:
                    output += str(num) + "ms"
            case 2:
                contains_hours = False
                contains_minutes = False
                #Hours
                val = num // 3600000
                if val > 0:
                    output += str(val) + ":"
                    num %= 3600000
                    contains_hours = True
                #Minutes
                val = num // 60000
                if val > 0:
                    output += str(val) + ":"
                    num %= 60000
                    contains_minutes = True
                elif contains_hours:
                    output += "00:"
                #Seconds
                val = num // 1000
                if val > 0:
                    output += str(val) + "."
                    num %= 1000
                elif contains_minutes or contains_hours:
                    output += "00."
                else:
                    output += "0."
                #Milliseconds
                if num > 0:
                    output += str(num)
                else:
                    output += "000"
        return output.upper() if return_format == 3 else output
    
    def translateTimeToString(self, num):
        output = ""
        match self.input_unit:
            case "ms":
                pass
            case "s":
                num *= 1000
            case "m":
                num *= 60000
            case "_":
                raise Exception("Invalid input type [ms/s/m]")
        num = int(num)
        match self.return_format:
            case 1 | 3:
                #Hours
                val = num // 3600000
                if val > 0:
                    output += str(val) + "h "
                    num %= 3600000
                #Minutes
                val = num // 60000
                if val > 0:
                    output += str(val) + "m "
                    num %= 60000
                #Seconds
                val = num // 1000
                if val > 0:
                    output += str(val) + "s "
                    num %= 1000
                #Milliseconds
                if num > 0:
                    output += str(num) + "ms"
            case 2:
                contains_hours = False
                contains_minutes = False
                #Hours
                val = num // 3600000
                if val > 0:
                    output += str(val) + ":"
                    num %= 3600000
                    contains_hours = True
                #Minutes
                val = num // 60000
                if val > 0:
                    output += str(val) + ":"
                    num %= 60000
                    contains_minutes = True
                elif contains_hours:
                    output += "00:"
                #Seconds
                val = num // 1000
                if val > 0:
                    output += str(val) + "."
                    num %= 1000
                elif contains_minutes or contains_hours:
                    output += "00."
                else:
                    output += "0."
                #Milliseconds
                if num > 0:
                    output += str(num)
                else:
                    output += "000"
        return output.upper() if self.return_format == 3 else output
    
# t = StringToTime(input_unit="s", input_format=0, return_unit="s", return_type="float", return_format=1)
# test = t.translateTimeToString(32500)
# test2 = t.translate(test)
# print(test)
# print(test2)