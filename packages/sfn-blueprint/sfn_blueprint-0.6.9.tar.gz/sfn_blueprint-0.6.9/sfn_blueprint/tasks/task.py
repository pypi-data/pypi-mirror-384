class Task:
    def __init__(self, description: str, data=None, path: str = None, task_type: str = None, category: str = None, analysis=None, code=None):
        self.description = description
        self.data = data
        self.path = path
        self.task_type = task_type  # e.g., 'feature_suggestion', 'data_quality', 'performance_optimization'
        self.category = category    # Domain category of the data/task
        self.analysis = analysis
        self.code = code