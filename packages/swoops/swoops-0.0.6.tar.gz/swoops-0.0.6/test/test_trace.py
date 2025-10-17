"""
Written by Jason Krist
06/03/2024
"""

import test_cases as tc

def print_trace(trace):
    print(f"    trace = {trace}")
    attr_list = ["attr_obj", "obj_class", "obj_id", "pairs","list"]
    for attr_name in attr_list:
        attr_val = getattr(trace, attr_name)
        print(f"    {attr_name} = {attr_val}")
    print(f"    head = {trace.head}")

if __name__ == "__main__":
    ses2 = tc.session_2()
    proj1 = ses2.projects[1]
    print(f"project 1 trace: {proj1._trace}")
    wf1 = proj1.workflows[1]
    print(f"workflow 1 trace: {wf1._trace}")
    print_trace(wf1._trace)
    wf1_fromtrace = wf1._trace.get_obj(ses2)
    print(f"workflow 1 from trace: {wf1_fromtrace}")
    wf_contains_proj = wf1._trace.contains(proj1._trace)
    proj_contains_wf = proj1._trace.contains(wf1._trace)
    print(f"Workflow Contains Proj: {wf_contains_proj}")
    print(f"Proj Contains Workflow: {proj_contains_wf}")
    inp_10 = wf1.inputs[10]
    print(f"input 10 trace: {inp_10._trace}")
    for attr in dir(inp_10):
        if attr.startswith("_"):
            continue
        trace = inp_10._trace.attr(attr)
        print(f"\nInput 10 attr {attr} trace")
        print_trace(trace)
    #integrator = um.Integrator(ses2)

