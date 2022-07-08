
from collections.abc import Iterable

class Visitor:

    """A visitor class to visit elements of nested containers

    Example:
    --------
        v = Visitor(
            visit_types=(list, tuple)
        )
        # Apply a function to each element (return None)
        v.apply([[11, 12, 13], 2, [311, [321, 322, 323], 33], 3], print)

        # Flatten the container
        v.flatten([[11, 12, 13], 2, [311, [321, 322, 323], 33], 3])
        >>> [11, 12, 13, 2, 311, 321, 322, 323, 33, 3]
    """

    def __init__(self, use_attr=None, use_func=None,
                 visit_types=None, visit_func=None, visit_with_attr=None, visit_iterables=None,
                 iter_attr=None, iter_item=None, iter_func=None):
        
        # Iteration:
        #   iter([1, 2, 3])
        #   myobj.things
        #   my_generator([1,2,3])
        #   myobj["things"]

        # Iteration check
        #   
        self.use_attr = use_attr
        self.use_func = use_func
        self.iter_func = iter_func

        self.visit_funcs = []
        if visit_types is not None:
            self.visit_funcs.append(lambda cont: isinstance(cont, visit_types))

    def flatten(self, cont):
        """Turn nested container to flat container
        
        Example:
        --------
            v = Visitor(visit_types=(list,))
            v.flatten([[1,2,3], 4, [5,6,7]])
            >>> [1,2,3,4,5,6,7]
        """
        if not self.is_visitable(cont):
            # End up here only if first level of recursion
            return [cont]

        tgtcont = []
        for key, subcont in self.iter(cont):

            if self.is_visitable(subcont):
                out = self.flatten(subcont)
            else:
                out = [subcont]
            tgtcont += out
        return tgtcont

    def assign_elements(self, cont, func):
        "Assign function to the elements of the container"
        # cont: [1, [21, 22, 23], 3]
        #   iter 0:
        #       cont[0] = func(1)
        #   iter 1:
        #       subcont = [21, 22, 23]
        #       ....    
        # cont: {"a": 1, "b": {"ba": 1, "bb": 2, "bc": 3}, "c": 2}
        #   iter 0:
        #       cont["a"] = func(1)
        #   iter 1:
        #       subcont = {"ba": 1, "bb": 2, "bc": 3}
        #       ....    
        if not self.is_visitable(cont):
            # End up here only if first level of recursion
            raise TypeError(f"Values of {cont} cannot be set anywhere. The object must be a visitable")

        for key, obj in self.iter(cont):
            if self.is_visitable(obj):
                self.assign_elements(obj, func)
            else:
                value = func(obj)
                self._assign_value(cont, key, value)

    def _assign_value(self, cont, key, value):
        # list: cont=[1, 2, 3], key=0, value=5
        #   cont[0] = 5
        # dict: cont=[1, 2, 3], key=0, value=5

        if self.use_attr:
            # cont = Namespace(myattr=[1,2,3]) (key=0, value=-1)
            getattr(cont, self.use_attr)[key] = value
        else:
            # cont = [1,2,3] (key=0, value=-1)
            # cont = {"a":1, "b":2} (key="a", value=-1)
            cont[key] = value

    def reduce(self, cont, func):
        args = []   
        for key, subobj in self.iter(cont):
            if not self.is_visitable(subobj):
                # subobj = 5
                args.append(subobj)
            elif self.has_sub_containers(subobj):
                # subobj = [1, [2, 3], 4]
                value = self.reduce(subobj, func)
                args.append(value)
            else:
                # # subobj = [1, 2, 3, 4]
                subargs = [val for key, val in self.iter(subobj)]
                value = func(*subargs)
                args.append(value)
        # Now should be inner
        # cont = [3, 3]
        return func(*args)

    def has_sub_containers(self, obj):
        if not self.is_visitable(obj):
            return False
        return any(
            self.is_visitable(subobj)
            for key, subobj in self.iter(obj)
        )

    def apply(self, cont, func):
        "Apply a function to each container"
        func(cont)
        for key, subcont in self.iter(cont):
            if self.is_visitable(subcont):
                # Container
                self.apply(subcont, func)
            else:
                # Actual element
                pass

    def iter(self, obj):
        # List:
        #   [1,2,3]
        #   1, 2, 3
        # Dict:
        #   {"a": 1, "b": 2, "c": 3}
        #   1, 2, 3

        cont = self._get_container(obj)

        if self.iter_func:
            return self.iter_func(cont)

        # Try to figure it out
        if isinstance(cont, dict):
            return cont.items()
        else:
            # Includes lists, tuples, sets etc
            return enumerate(cont)
            
    def _get_container(self, obj):
        if self.use_attr:
            return getattr(obj, self.use_attr)
        else:
            return obj

    def is_visitable(self, obj):
        if len(self.visit_funcs) == 0:
            cont = self._get_container(obj)
            return isinstance(cont, Iterable)
        return all(
            func(obj)
            for func in self.visit_funcs
        )
