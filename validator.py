import json

class Validator:

    def validate(self, plan):

        if not isinstance(plan, list):
            raise ValueError("Plan must be a list")

        valid_actions = []

        for action in plan:

            if "action" not in action:
                print("Missing action field")
                continue

            valid_actions.append(action)

        return valid_actions