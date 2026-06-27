from planner import Planner
from validator import Validator

planner = Planner()

validator = Validator()

task = input("Task : ")

plan = planner.plan(task)

plan = validator.validate(plan)

print(plan)