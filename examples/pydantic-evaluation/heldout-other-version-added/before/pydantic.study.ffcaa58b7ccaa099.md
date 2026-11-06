!!! note "On inheritance"
    A model validator defined in a base class will be called during the validation of a subclass instance.

    Overriding a model validator in a subclass will override the base class' validator, and thus only the subclass' version of said validator will be called.
