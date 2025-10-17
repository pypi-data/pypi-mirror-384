"""
Written by Jason Krist
06/03/2024
"""

from os import path
import sys
from pandas import DataFrame
import numpy as np
import math as m
from typing import Tuple

testdir = path.dirname(path.realpath(__file__))
appendpath = path.realpath(path.join(testdir, "../src"))
#print(appendpath)
sys.path.insert(0, appendpath)

from swoops import structures as st  # type: ignore # pylint: disable=E0611,E0401,C0413


def add_inputs(wf, num:int):
    for i in range(num):
        wf.new(
            st.Input,
            name=f"input {i+1}",
            value=float(i),
            lb=i - 1.1,
            ub=i + 1.1,
        )

def session_0():
    """add a dataframe object to workflow"""
    ses0 = session_1()
    wf1 = ses0.projects[1].workflows[1]
    dic = {"col1": [0, 1, 2, 3], "col2": [1, 2, 3, 5],
            "col3": ["uno","dos","tres","cuatro"],
            "col4": [1.1, 0.1, 200, 40]}
    df = DataFrame(data=dic)
    setattr(wf1, "DF", df)
    return ses0

def session_1():
    """session with 1 proj and 1 wf"""
    ses0 = st.Session(0)
    proj0 = ses0.new(st.Project, name="Project Name 1")
    wf1 = proj0.new(st.Workflow, name="Workflow Name 1_1")
    node1 = wf1.new(st.Task, name="task 1")
    wf1.new(st.Task, name="task 2")
    add_inputs(wf1, 10)
    return ses0

def session_2():
    """session with 2 proj and 2 wfs each and 2 studies each"""
    ses0 = session_1()
    proj0 = ses0.projects[1]
    wf2_2 = proj0.new(st.Workflow, name="Workflow Name 1_2")
    proj1 = ses0.new(st.Project, name="Project Name 2")
    wf2_1 = proj1.new(st.Workflow, name="Workflow Name 2_1")
    add_inputs(wf2_1, 8)
    wf2_2 = proj1.new(st.Workflow, name="Workflow Name 2_2")
    add_inputs(wf2_2, 15)
    return ses0


def session_3():
    """session with 1 proj and 1 wf and 10000 inputs"""
    ses0 = st.Session(0)
    proj0 = ses0.new(st.Project, name="Project Name 1")
    wf1 = proj0.new(st.Workflow, name="Workflow Name 1_1")
    node1 = wf1.new(st.Task, name="task 1")
    wf1.new(st.Task, name="task 2")
    add_inputs(wf1, 10000)
    #in1 = wf1.inputs[1]
    #print(in1.__class__.__annotations__)
    return ses0

def sellar_1(x, z, y_2)->np.ndarray:
    y_1 = np.array([(z[0] ** 2 + z[1] + x[0] - 0.2 * y_2[0]) ** 0.5])
    return y_1

def sellar_2(z, y_1)->np.ndarray:
    y_2 = np.array([abs(y_1[0]) + z[0] + z[1]])
    return y_2

def sellar_system(x, z, y_1, y_2)->Tuple[np.ndarray, np.ndarray, np.ndarray]:
    obj = np.array([x[0] ** 2 + z[1] + y_1[0] ** 2 + m.exp(-y_2[0])])
    c_1 = np.array([3.16 - y_1[0] ** 2])
    c_2 = np.array([y_2[0] - 24.0])
    return obj, c_1, c_2

def gemseo_sellar_problem_old_v1():
    """Sellar Problem"""
    session = st.Session(0)
    proj = session.new(st.Project, name="Sellar Problem")
    wf = proj.new(st.Workflow, name="Sellar Workflow")

    # Tasks
    task1 = wf.new(st.Task, name="Sellar1")
    task2 = wf.new(st.Task, name="Sellar2")
    task3 = wf.new(st.Task, name="SellarSystem")

    # Methods
    print(f"file: {path.abspath(__file__)}")
    method1 = wf.new(st.Method, name=task1.name, file=path.abspath(__file__), function='sellar_1')
    method2 = wf.new(st.Method, name=task2.name, file=path.abspath(__file__), function='sellar_2')
    method3 = wf.new(st.Method, name="sellar_system", file=path.abspath(__file__), function='sellar_system')

    # X Variable
    in1 = wf.new(st.Input, name="x", value = 1.0, lb = 0.0, ub = 10.0)
    wf.assign(task1, in1)
    wf.assign(task3, in1)

    # Z Variable
    in2 = wf.new(st.Input, name="z", value = [4.0, 3.0], lb = [-10.0, 0.0], ub = [10.0, 10.0])
    wf.assign(task1, in2)
    wf.assign(task2, in2)
    wf.assign(task3, in2)

    # Y1 Variable
    in3 = wf.new(st.Input, name="y_1", value = 1.0, lb = -100.0, ub = 100.0)
    out1 = wf.new(st.Output, name="y_1")
    wf.assign(task1, out1)
    wf.assign(task2, in3)
    wf.assign(task3, in3)

    # Y2 Variable
    in4 = wf.new(st.Input, name="y_2", value = 1.0, lb = -100.0, ub = 100.0)
    out2 = wf.new(st.Output, name="y_2")
    wf.assign(task1, in4)
    wf.assign(task2, out2)
    wf.assign(task3, in4)

    # Sellar System / Group?

    # Constraints and Objectives
    out3 = wf.new(st.Output, name="c_1")
    con1 = wf.new(st.Constraint, name=out3.name, ub=0.0)
    wf.assign(con1, out3)
    wf.assign(task3, out3)
    out4 = wf.new(st.Output, name="c_2")
    con2 = wf.new(st.Constraint, name=out4.name, ub=0.0)
    wf.assign(con2, out4)
    wf.assign(task3, out4)
    out5 = wf.new(st.Output, name="obj")
    obj1 = wf.new(st.Objective, name=out5.name)
    wf.assign(obj1, out5)
    wf.assign(task3, out5)

    return session


def session_4():
    """session with 1 proj and 1 wf and 10000 inputs"""
    ses0 = st.Session(0)
    proj0 = ses0.new(st.Project, name="Project Name 1")
    wf1 = proj0.new(st.Workflow, name="Workflow Name 1_1")
    last_task = None
    for i in range(10):
        task = wf1.new(st.Task, name=f"Task {i}")
        if i > 0:
            wf1.new(st.Dependency, source=last_task, destinations=[task], name=f"Dep {i}")
        last_task = task
    add_inputs(wf1, 15)
    #in1 = wf1.inputs[1]
    #print(in1.__class__.__annotations__)
    return ses0

def session_5():
    """session with 1 proj and 1 wf and 10000 inputs"""
    ses = session_2()
    sellar_ses = gemseo_sellar_problem()
    sellar_project = sellar_ses.projects[1]
    #print(f"   Before Add: {sellar_project.workflows[1].outputs}")
    ses.add(sellar_project)
    #print(f"   After Add: {sellar_project.workflows[1].outputs}")
    return ses


def gemseo_sellar_problem():
    """Sellar Problem"""
    session = st.Session(0)
    proj = session.new(st.Project, name="Sellar Problem")
    wf = proj.new(st.Workflow, name="Sellar Workflow")
    scriptpath = path.abspath(__file__)

    # Input Variables
    in1 = wf.new(st.Input, name="x", value = 1.0, lb = 0.0, ub = 10.0)
    in2 = wf.new(st.Input, name="z", value = [4.0, 3.0], lb = [-10.0, 0.0], ub = [10.0, 10.0])
    in3 = wf.new(st.Input, name="y_1", value = 1.0, lb = -100.0, ub = 100.0)
    in4 = wf.new(st.Input, name="y_2", value = 1.0, lb = -100.0, ub = 100.0)

    # Output Variables
    out1 = wf.new(st.Output, name="y_1")
    out2 = wf.new(st.Output, name="y_2")
    out3 = wf.new(st.Output, name="c_1")
    out4 = wf.new(st.Output, name="c_2")
    out5 = wf.new(st.Output, name="obj")

    # Constraints and Objectives
    con1 = wf.new(st.Constraint, name=out3.name, ub=0.0, output=out3)
    con2 = wf.new(st.Constraint, name=out4.name, ub=0.0, output=out4)
    obj1 = wf.new(st.Objective, name=out5.name, output=out5)

    # Task and Method 1
    task1 = wf.new(st.Task, name="Sellar1")
    method1 = wf.new(st.Method, name=task1.name, file=scriptpath, function='sellar_1')
    task1.methods = [method1]
    task1.inputs = [in1, in2, in4]
    task1.outputs = [out1]

    # Task and Method 2
    method2 = wf.new(st.Method, name="Sellar2", file=scriptpath, function='sellar_2')
    task2 = wf.new(st.Task, name="Sellar2", methods=[method2], inputs=[in2, in3], outputs=[out2])

    # Task and Method 3
    task3 = wf.new(st.Task, name="SellarSystem")
    method3 = wf.new(st.Method, name=task3.name, file=scriptpath, function='sellar_system')
    task3.methods = [method3]
    task3.inputs = [in1, in2, in3, in4]
    task3.outputs = [out3, out4, out5]

    # Sellar System / Group?

    return session

def session_6():
    ses0 = gemseo_sellar_problem()
    proj0 = ses0.new(st.Project, name="Project Name 1")
    wf1 = proj0.new(st.Workflow, name="Workflow Name 1_1")
    last_task = None
    for i in range(1,10):
        task = wf1.new(st.Task, name=f"Task {i}")
        if i > 0:
            wf1.new(st.Dependency, source=last_task, destinations=[task], name=f"Dep {i}")
        last_task = task
    task1 = wf1.new(st.Task, name=f"Task Extra 1")
    wf1.new(st.Dependency, destinations=[task1], name=f"Dep Extra 1")
    wf1.new(st.Dependency, name=f"Dep Extra 2")
    add_inputs(wf1, 15)
    return ses0

