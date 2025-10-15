class BirdbrainUtility:
    @classmethod
    def is_none_or_empty(self, s):
        if s is None or s == "":
            return True
        else:
            return False

    @classmethod
    def bounds(self, input, input_min, input_max, pass_through_input = None):
        #if pass_through_input is not None and (input == pass_through_input): return int(input)

        if int(input) < int(input_min): return int(input_min)
        if int(input) > int(input_max): return int(input_max)

        return int(input)

    @classmethod
    def decimal_bounds(self, input, input_min, input_max, pass_through_input = None):
        #if pass_through_input is not None and (input == pass_through_input): return int(input)

        if float(input) < float(input_min): return float(input_min)
        if float(input) > float(input_max): return float(input_max)

        return float(input)


    @classmethod
    def flatten_string(self, original_list, divider = "/"):
        if isinstance(original_list[0], list): original_list = original_list[0]

        original_list = [item for item in original_list]

        s = ""
        for element in list(original_list):
            if isinstance(element, str):
                s += str(element) + divider
            elif isinstance(element, int):
                s += str(element) + divider
            else:
                for sub_element in element:
                    s += str(sub_element) + divider

        return(s[:-1])
