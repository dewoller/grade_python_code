import dspy
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import json
from matplotlib import pyplot as plt
import toml

def create_dynamic_signature_class(class_name, doc_string, input_fields, output_fields):
    """
    Create a dynamic signature class with given input and output fields.
    
    Args:
    - class_name: The name of the class to be created.
    - input_fields: A dictionary where keys are field names and values are descriptions.
    - output_fields: A dictionary where keys are field names and values are descriptions.
    
    Returns:
    - A dynamically created class.
    """
    # Define the fields
    fields = {}
    
    # Add input fields
    for field_name, description in input_fields.items():
        fields[field_name] = dspy.InputField(desc=description)
    
    # Add output fields
    for field_name, description in output_fields.items():
        fields[field_name] = dspy.OutputField(desc=description)

    fields['__doc__'] = doc_string
    
    # Create the class dynamically
    new_class = type(class_name, (dspy.Signature,), fields)
    return new_class

def create_dynamic_signature_instance(class_name, DynamicSignatureClass):
    """
    Create a dynamic signature instance with from a given dynamic signature class. 
    
    Returns:
    - An instance of a dynamically created class with a `forward` method.
    """
    
    # Define the dynamic module class with a forward method
    dynamic_instance = type(
        class_name + "Module",
        (dspy.Module,),
        {
            '__init__': lambda self: setattr(self, 'prog', dspy.ChainOfThought(DynamicSignatureClass)),
            'forward': lambda self, *args, **kwargs: self.prog(*args, **kwargs)
        }
    )
    
    # Instantiate and return the dynamic module class
    return dynamic_instance()














# robust number parser
def parse_integer_answer(answer, only_first_line=True):
    try:
        if only_first_line:
            answer = answer.strip().split('\n')[0]

        # find the last token that has a number in it
        answer = [token for token in answer.split() if any(c.isdigit() for c in token)][-1]
        answer = answer.split('.')[0]
        answer = answer.split('/')[0]
        answer = ''.join([c for c in answer if c.isdigit()])
        answer = int(answer)

    except (ValueError, IndexError):
        # print(answer)
        answer = 0
    
    return answer

def numeric_metric_out_of_10(example, pred, trace=None):
    # distance from student mark to predicted mark, out of 10
    distance = abs( example.student_mark_normalized - int(parse_integer_answer(str(pred.student_mark_out_of_10))))
    if trace is not None: return distance <0.5 
    #else return score out of 10
    return (10-distance)/10




# Define the signature for automatic assessments.
class Assess(dspy.Signature):
    """Assess the quality of a tweet along the specified dimension."""

    assessed_text = dspy.InputField()
    assessment_question = dspy.InputField()
    assessment_answer = dspy.OutputField(desc="Yes or No")




def plot_results(results):
    
    x = [int(item[0].student_mark_normalized) for item in results]
    y = [parse_integer_answer(item[1].student_mark_out_of_10) for item in results]


    # Create the plot
    plt.figure(figsize=(10, 6))
    
    jitter_amount = 0.2
    x_jittered = x + np.random.normal(0, jitter_amount, len(x))
    y_jittered = y + np.random.normal(0, jitter_amount, len(y))

    plt.scatter(x_jittered, y_jittered, color='blue', alpha=0.6, s=100)

    # Customize the plot
    plt.title('Student Mark Normalized vs Student Mark Out of 10', fontsize=16)
    plt.xlabel('Student Mark Normalized', fontsize=12)
    plt.ylabel('Student Mark Out of 10', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)

    # Add a diagonal line for reference (perfect correlation)
    plt.plot([0, 10], [0, 10], color='red', linestyle='--', alpha=0.5, label='Perfect Correlation')

    plt.legend()

    # Show the plot
    plt.tight_layout()
    plt.show()




def read_from_toml( file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        data = toml.load(f)
    return data

def create_dynamic_marker_classes_from_toml( file_path: str):
    data = read_from_toml(file_path)
    markers={}
    for name, config in data.items():
        marker = create_dynamic_signature_class(
            name,
            config['docstring'],
            config['input_fields'],
            config['output_fields']
        )
        markers[name] = {
            'docstring': config['docstring'],
            'input_fields': config['input_fields'],
            'output_fields': config['output_fields'],
            'marker_class': marker
        }
    return markers

def create_dynamic_markers_from_toml( file_path: str):
    markers = create_dynamic_marker_classes_from_toml(file_path)
    for name, data in markers.items():
        data['marker'] = create_dynamic_signature_instance( name, data['marker_class'] )
    return( markers)


def dump_single_evaluation(evaluation):
    example_json = json.dumps(evaluation[0].toDict())
    prediction_json = json.dumps(evaluation[1].toDict())
    confidence = str(evaluation[2])
    return example_json, prediction_json, confidence


def write_evaluations_to_csv(marker_name, evaluations, file_path=None):
    if file_path is None:
        file_path = f'./evaluations/{marker_name}_evaluations.csv' 
    data = []
    for evaluation in evaluations:
        example_json, prediction_json, confidence = dump_single_evaluation(evaluation)
        data.append({
            'MarkerName': marker_name,
            'Example': example_json,
            'Prediction': prediction_json,
            'Confidence': confidence
        })
    
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)           
    
    

#%% prepare data

def exemplify_data( dataset_details: pd.DataFrame):
    dataset_details_ex =[]
    for index, row in dataset_details.iterrows():
        ex = dspy.Example(base=row.to_dict())
        dataset_details_ex.append( ex )
    return dataset_details_ex

############################################
### Split data
############################################

def split_data( dataset_details_ex: List[dspy.Example], inputs: List[str], n=None):
    
    if (n==None):
        n = int( len(dataset_details_ex)/10)

    from sklearn.model_selection import train_test_split
    # Splitting data
    train, temp = train_test_split(dataset_details_ex, test_size=0.2, random_state=42)  
    val, dev = train_test_split(temp, test_size=0.5, random_state=42)    

    # # Output the lengths of each set
    # print("Train size:", len(train))
    # print("val size:", len(val))
    # print("Dev size:", len(dev))

    # inputs = ['code','subquestion','question_text']
    # n=100
    trainset = [x.with_inputs(*inputs) for x in train[1:n*8]]
    valset = [x.with_inputs(*inputs) for x in val[1:n]]
    devset = [x.with_inputs(*inputs) for x in dev[1:n]]
    return trainset, valset, devset

   