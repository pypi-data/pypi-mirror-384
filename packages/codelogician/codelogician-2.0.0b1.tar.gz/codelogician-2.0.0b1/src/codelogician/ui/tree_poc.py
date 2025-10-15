from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Tree, Static
from textual.widgets.tree import TreeNode


from strategy.metamodel import MetaModel
from strategy.state import PyIMLStrategyState

class MyTree(Tree):
    """  """
    def __init__(self, label, mmodel:MetaModel, tree_type:str='models'):
        """ ctor """
        super().__init__(label, id="tree")
        self.mmodel = mmodel
        self.root.expand()

        paths = self.mmodel.get_paths_with_dirs()

        def addElements(d, root : TreeNode):
            for key, value in d.items():
                if key == '<files>':
                    for model in value:
                        if tree_type == 'models':
                            root.add_leaf(model.path)
                        elif tree_type == 'dependents':
                            temproot = root.add(model.path)
                            for d in model.dependencies:
                                temproot.add_leaf(d.path)
                        elif tree_type == 'ascendents':
                            temproot = root.add(model.path)
                            for d in model.rev_dependencies:
                                temproot.add_leaf(d.path)
                else:
                    root = root.add(key)
                    addElements(value, root)
        
        addElements(paths, self.root)

class TreeApp(App):
    CSS_PATH = "tree.tcss"

    def __init__(self, mmodel:MetaModel):
        super().__init__()
        self.mmodel = mmodel

    def compose(self) -> ComposeResult:
        yield MyTree(self.mmodel.src_dir, self.mmodel)
        yield Static("Model view", classes="box", id="model")

    @on(Tree.NodeSelected, "#tree") 
    def update_model(self, event):
        def get_full_path(node, path):
            if node.parent is None:
                return path
            else:
                return get_full_path(node.parent, node.parent.label + "/" + path)

        model_view = self.query_one("#model")
        fullpath = str(get_full_path(event.node, event.node.label))

        fullpath = fullpath.replace(self.mmodel.src_dir + '/', '')
        
        model = self.mmodel.get_model_by_path(fullpath)
        if model:
            model_view.update(model)
        else:
            model_view.update(fullpath)

if __name__ == "__main__":

    state = PyIMLStrategyState.from_directory("data/code2")
    mmodel = state.curr_meta_model
    
    #print(mmodel.get_paths_with_dirs())

    app = TreeApp(mmodel)
    app.run()