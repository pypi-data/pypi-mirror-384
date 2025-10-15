import json

from django import forms

from django_blocknote.widgets import BlockNoteWidget


class BlockNoteUserFormMixin:
    """
    Cooperative form mixin to automatically configure BlockNote widgets with user templates.

    This mixin automatically detects BlockNote widgets in form fields and configures
    them with user context for template personalization and user-specific functionality.
    It's designed to work cooperatively with other form mixins without conflicts.

    Key Features:
    - Automatic BlockNote widget detection and configuration
    - User context passing for widget personalization
    - CSV to JSON conversion for aliases fields
    - Cooperative inheritance design
    - Comprehensive debugging support
    - Graceful handling of missing user context

    Usage:
        class DocumentForm(BlockNoteUserFormMixin, forms.ModelForm):
            content = forms.CharField(widget=BlockNoteWidget())

            class Meta:
                model = Document
                fields = ['title', 'content']

        # Combined with other mixins
        class ArticleForm(TagMeModelFormMixin, BlockNoteUserFormMixin, forms.ModelForm):
            content = forms.CharField(widget=BlockNoteWidget())
            tags = TagMeCharField()

            class Meta:
                model = Article
                fields = ['title', 'content', 'tags']

    Widget Configuration:
    Automatically configures BlockNote widgets with:
    - User context for template personalization
    - Field name for widget identification
    - Any additional BlockNote-specific attributes

    Form Integration:
    The mixin expects 'user' from form kwargs (provided by view mixins):
    - Works with authenticated and anonymous users
    - Gracefully handles missing user context
    - Preserves user context for other mixins

    Cooperative Design:
    - Uses shared user extraction pattern
    - Removes 'user' from kwargs after all mixins process it
    - Maintains compatibility with Django's form system
    - Safe to use in any order with other cooperative mixins

    Performance:
    - Minimal overhead during form initialization
    - Widget configuration happens only once
    - No additional database queries
    - Thread-safe operation

    Debugging:
    Set `_debug_widget_config = True` on form class to enable detailed
    logging of widget configuration for development and troubleshooting.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize form and configure BlockNote widgets with user context.

        Extracts user from kwargs and configures all BlockNote widgets
        in the form with appropriate user context. Uses cooperative
        inheritance pattern to work seamlessly with other form mixins.

        Args:
            *args: Variable length argument list for parent form
            **kwargs: Keyword arguments including:
                - user: Optional user object for widget personalization

        Cooperative Behavior:
        - Checks if user was already extracted by another mixin
        - Extracts user from kwargs if not already available
        - Stores user reference for widget configuration
        - Calls super().__init__() appropriately

        User Sharing Strategy:
        - First mixin to run extracts user with pop() and stores it
        - Subsequent mixins check for existing self.user attribute
        - This prevents TypeError from unexpected kwargs in Django forms

        Widget Processing:
        After form initialization, automatically:
        - Identifies all BlockNote widgets in form fields
        - Configures widgets with user context
        - Adds field metadata for widget functionality
        - Provides debugging information if enabled
        """
        # Check if user was already extracted by another mixin
        if hasattr(self, "user"):
            # Another mixin already extracted the user - use that
            user = self.user
        else:
            # First mixin to run - extract user from kwargs
            user = kwargs.pop("user", None)
            self.user = user

        # Initialize parent form
        super().__init__(*args, **kwargs)

        # Configure all BlockNote widgets with user context
        self._configure_blocknote_widgets()

    def _configure_blocknote_widgets(self):
        """
        Find and configure all BlockNote widgets with user context.

        Iterates through all form fields to identify BlockNote widgets
        and configures them with user context and field metadata.
        This enables user-specific templates and personalization features.

        Widget Configuration:
        For each BlockNote widget, adds:
        - User context for template selection
        - Field name for widget identification
        - Any additional BlockNote-specific attributes

        Safety Features:
        - Gracefully handles missing user context
        - Only modifies BlockNote widgets
        - Uses widget.attrs.update() for safe attribute merging
        - Preserves existing widget attributes

        Debug Support:
        - Counts configured widgets for logging
        - Provides detailed configuration information
        - Logs user context for troubleshooting

        Performance:
        - Single pass through form fields
        - Minimal processing overhead
        - No database queries
        """
        if not self.user:
            # No user context available - widgets will use default behavior
            return

        configured_count = 0

        for field_name, field in self.fields.items():
            if isinstance(field.widget, BlockNoteWidget):
                # Configure widget with user context and metadata
                field.widget.attrs.update(
                    {
                        "user": self.user,
                        "field_name": field_name,
                    },
                )
                configured_count += 1

                # Debug logging in development
                if hasattr(self, "_debug_widget_config"):
                    print(
                        f"✅ Configured BlockNote widget '{field_name}' "
                        f"for user {self.user.username}",
                    )

        # Optional debug output
        if configured_count > 0 and hasattr(self, "_debug_widget_config"):
            print(
                f"🎯 Configured {configured_count} BlockNote widget(s) "
                f"for user {self.user.username}",
            )

    def clean_aliases(self):
        """
        Convert CSV string input to JSON string for storage.

        Provides automatic conversion of comma-separated alias input
        to JSON format for database storage. Handles various input
        formats and provides robust error handling.

        Returns:
            str: JSON-formatted string of aliases

        Input Handling:
        - Empty input: Returns empty JSON array "[]"
        - CSV string: Converts to JSON array of trimmed strings
        - Existing JSON: Validates and returns as-is
        - Invalid input: Returns empty JSON array

        Examples:
            "tag1, tag2, tag3" -> '["tag1", "tag2", "tag3"]'
            '["existing", "json"]' -> '["existing", "json"]'
            "" -> "[]"
            None -> "[]"

        Error Handling:
        - Gracefully handles malformed JSON
        - Strips whitespace from CSV entries
        - Filters out empty strings
        - Provides fallback for unexpected input types
        """
        aliases = self.cleaned_data.get("aliases")

        if not aliases:
            return "[]"  # Empty JSON array

        # Handle string input (CSV from forms)
        if isinstance(aliases, str):
            # Check if it's already valid JSON
            try:
                parsed = json.loads(aliases)
                if isinstance(parsed, list):
                    return aliases  # Already valid JSON
            except (json.JSONDecodeError, ValueError):
                pass

            # Treat as CSV and convert to JSON
            alias_list = [
                alias.strip() for alias in aliases.split(",") if alias.strip()
            ]
            return json.dumps(alias_list)

        # Fallback for unexpected types
        return "[]"


class BlockNoteUserFormsetMixin:
    """
    Cooperative formset mixin to handle user context for forms with BlockNote widgets.

    This mixin enables BlockNote functionality in Django formsets and inline
    formsets by ensuring user context is properly passed to all forms within
    the formset. Essential for bulk editing and inline scenarios.

    Key Features:
    - Automatic user context propagation to all formset forms
    - Compatible with formset_factory and inlineformset_factory
    - Cooperative inheritance design
    - Works with Django admin inline formsets
    - Maintains consistency with single form behavior

    Usage:
        # With formset_factory
        SectionFormSet = formset_factory(
            SectionForm,
            formset=BlockNoteUserFormsetMixin
        )
        formset = SectionFormSet(user=request.user)

        # With inlineformset_factory
        SectionInlineFormSet = inlineformset_factory(
            Article, Section,
            form=SectionForm,
            formset=BlockNoteUserFormsetMixin
        )

        # In views
        class ArticleUpdateView(BlockNoteUserViewMixin, UpdateView):
            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                context['sections'] = SectionInlineFormSet(
                    instance=self.object,
                    **self.get_formset_kwargs()  # Includes user context
                )
                return context

    Integration Points:
    - get_form_kwargs(): Passes user to individual forms
    - _construct_form(): Ensures user context during form construction
    - Cooperative with view mixin get_formset_kwargs()

    Compatibility:
    - Works with any Django formset type
    - Compatible with third-party formset libraries
    - Maintains Django's formset API
    - Safe to combine with other formset mixins

    Performance:
    - Minimal overhead per form
    - No additional database queries
    - Efficient user context propagation
    - Thread-safe operation
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize formset and prepare user context for all forms.

        Extracts user context from kwargs and stores it for propagation
        to all forms in the formset. Uses cooperative inheritance to
        work with other formset mixins.

        Args:
            *args: Variable length argument list for parent formset
            **kwargs: Keyword arguments including:
                - user: Optional user object for form context

        Cooperative Behavior:
        - Extracts user from kwargs before super() call
        - Stores user reference for form construction
        - Maintains compatibility with Django's formset system
        - Safe to use with other formset mixins
        """
        # Extract user from kwargs BEFORE calling super()
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        """
        Pass user context to individual forms in the formset.

        Ensures that each form in the formset receives user context
        for proper BlockNote widget configuration. Called by Django
        during form construction for management forms and regular forms.

        Args:
            index (int): Index of the form in the formset

        Returns:
            dict: Form kwargs enhanced with user context

        Cooperative Behavior:
        - Calls super() if method exists (some formsets don't have it)
        - Only adds user if available
        - Maintains compatibility with custom formset implementations
        """
        # Handle cooperative inheritance - some formsets may not have this method
        kwargs = (
            super().get_form_kwargs(index)
            if hasattr(super(), "get_form_kwargs")
            else {}
        )

        # Add user context for BlockNote widgets in formset forms
        if self.user:
            kwargs["user"] = self.user

        return kwargs

    def _construct_form(self, i, **kwargs):
        """
        Ensure user context is passed during form construction.

        Provides a safety net to ensure user context is available
        during form construction, even if other methods don't
        properly propagate it. This ensures consistent behavior
        across different Django versions and formset types.

        Args:
            i (int): Index of the form being constructed
            **kwargs: Keyword arguments for form construction

        Returns:
            Form: Constructed form instance with user context

        Safety Features:
        - Only adds user if not already present
        - Gracefully handles missing user context
        - Maintains compatibility with Django's construction process
        """
        # Ensure user is passed when constructing forms
        if self.user and "user" not in kwargs:
            kwargs["user"] = self.user

        return super()._construct_form(i, **kwargs)


# Convenience mixins for common use cases
class BlockNoteFormMixin(BlockNoteUserFormMixin, forms.Form):
    """
    Complete form mixin combining BlockNote functionality with Django's Form.

    This is a convenience mixin that combines BlockNoteUserFormMixin with
    Django's base Form class. Use this as a drop-in replacement for
    forms.Form when you need BlockNote functionality.

    Usage:
        class DocumentForm(BlockNoteFormMixin):
            title = forms.CharField(max_length=200)
            content = forms.CharField(widget=BlockNoteWidget())

        # The form will automatically configure BlockNote widgets
        form = DocumentForm(user=request.user)

    Features:
    - All BlockNoteUserFormMixin functionality
    - Direct inheritance from forms.Form
    - Ready-to-use without additional base classes
    - Maintains compatibility with Django form ecosystem
    """


class BlockNoteModelFormMixin(BlockNoteUserFormMixin, forms.ModelForm):
    """
    Complete ModelForm mixin combining BlockNote functionality with Django's ModelForm.

    This is a convenience mixin that combines BlockNoteUserFormMixin with
    Django's ModelForm class. Use this as a drop-in replacement for
    forms.ModelForm when you need BlockNote functionality.

    Usage:
        class ArticleForm(BlockNoteModelFormMixin):
            class Meta:
                model = Article
                fields = ['title', 'content', 'summary']
                widgets = {
                    'content': BlockNoteWidget(),
                    'summary': BlockNoteWidget(),
                }

        # The form will automatically configure BlockNote widgets
        form = ArticleForm(instance=article, user=request.user)

    Features:
    - All BlockNoteUserFormMixin functionality
    - Direct inheritance from forms.ModelForm
    - Ready-to-use without additional base classes
    - Full ModelForm capabilities (save, validation, etc.)
    - Maintains compatibility with Django ModelForm ecosystem
    """


# Usage examples and documentation
"""
COMPLETE USAGE EXAMPLES:

1. Simple View + Form:
    
    class BlogPostForm(BlockNoteModelFormMixin):
        class Meta:
            model = BlogPost
            fields = ['title', 'content']
            widgets = {
                'content': BlockNoteWidget()
            }
    
    class BlogPostCreateView(BlockNoteUserViewMixin, CreateView):
        model = BlogPost
        form_class = BlogPostForm

2. Multiple BlockNote fields:
    
    class ArticleForm(BlockNoteModelFormMixin):
        intro = forms.CharField(widget=BlockNoteWidget())
        content = forms.CharField(widget=BlockNoteWidget())
        conclusion = forms.CharField(widget=BlockNoteWidget())
        
        class Meta:
            model = Article
            fields = ['title', 'intro', 'content', 'conclusion']

3. Inline formsets:
    
    class SectionForm(BlockNoteFormMixin):
        content = forms.CharField(widget=BlockNoteWidget())
    
    SectionFormSet = inlineformset_factory(
        Article, Section, 
        form=SectionForm,
        formset=BlockNoteUserFormsetMixin
    )
    
    class ArticleUpdateView(BlockNoteUserViewMixin, UpdateView):
        model = Article
        
        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['section_formset'] = SectionFormSet(
                instance=self.object,
                user=self.request.user
            )
            return context

4. Function-based views:
    
    def create_post(request):
        if request.method == 'POST':
            form = BlogPostForm(request.POST, user=request.user)
            if form.is_valid():
                form.save()
                return redirect('success')
        else:
            form = BlogPostForm(user=request.user)
        return render(request, 'create.html', {'form': form})

DEBUGGING:
Add _debug_widget_config = True to your form class to see configuration debug output.

    class MyForm(BlockNoteModelFormMixin):
        _debug_widget_config = True  # Enable debug output
        
        class Meta:
            model = MyModel
            fields = ['content']
"""
# class BlockNoteViewMixin:
#     """
#     Pure view mixin to automatically pass user to forms with BlockNote widgets.
#     Handles both regular forms and formsets/inlines.
#
#     Works with any Django view that has get_form method.
#     No inheritance conflicts - can be used with any generic view.
#
#     Usage:
#         class MyCreateView(BlockNoteUserViewMixin, CreateView):
#             model = MyModel
#             form_class = MyForm
#     """
#
#     def get_form_kwargs(self):
#         """Add user to form kwargs for BlockNote widgets (fallback method)"""
#         kwargs = super().get_form_kwargs()
#         if hasattr(self.request, "user") and self.request.user.is_authenticated:
#             kwargs["user"] = self.request.user
#         return kwargs
#
#     def get_form(self, form_class=None):
#         """
#         Enhanced form creation with BlockNote-specific validation and context.
#         Provides better error messages and conditional user injection.
#         """
#         if form_class is None:
#             form_class = self.get_form_class()
#
#         # Validate that form supports BlockNote functionality
#         # if not issubclass(form_class, BlockNoteUserFormMixin):
#         #     raise ImproperlyConfigured(
#         #         f"Form {form_class} must inherit from BlockNoteUserFormMixin "
#         #         f"to use BlockNote user templates."
#         #     )
#
#         form_kwargs = self.get_form_kwargs()
#
#         # Only add user if not already present (plays nice with other mixins)
#         if (
#             "user" not in form_kwargs
#             and hasattr(self.request, "user")
#             and self.request.user.is_authenticated
#         ):
#             form_kwargs["user"] = self.request.user
#
#         # Future: Add other BlockNote-specific context here
#         # form_kwargs["editor_permissions"] = self.get_editor_permissions()
#         # form_kwargs["template_context"] = self.get_template_context()
#
#         return form_class(**form_kwargs)

# def get_formset_kwargs(self):
#     """Add user to formset kwargs for inline forms with BlockNote widgets"""
#     kwargs = super().get_formset_kwargs()
#     if hasattr(self.request, "user") and self.request.user.is_authenticated:
#         kwargs["user"] = self.request.user
#     return kwargs

# class BlockNoteUserFormMixin:
#     """
#     Form mixin to automatically configure BlockNote widgets with user templates.
#     Automatically detects BlockNote widgets and passes user context via widget attrs.
#     Also handles CSV to JSON conversion for aliases fields.
#     """
#
#     def __init__(self, *args, **kwargs):
#         """Initialize form and configure BlockNote widgets with user"""
#         # Extract user from kwargs BEFORE calling super() to avoid TypeError
#         self.user = kwargs.pop("user", None)
#         super().__init__(*args, **kwargs)
#         # Configure all BlockNote widgets with user context
#         self._configure_blocknote_widgets()
#
#     def _configure_blocknote_widgets(self):
#         """Find and configure all BlockNote widgets with user context via attrs"""
#         if not self.user:
#             return
#         configured_count = 0
#         for field_name, field in self.fields.items():
#             if isinstance(field.widget, BlockNoteWidget):
#                 # Use widget.attrs pattern (standard Django approach)
#                 field.widget.attrs.update(
#                     {
#                         "user": self.user,
#                         "field_name": field_name,
#                     },
#                 )
#                 configured_count += 1
#                 # Debug logging in development
#                 if hasattr(self, "_debug_widget_config"):
#                     print(
#                         f"✅ Configured BlockNote widget '{field_name}' for user {self.user.username}",
#                     )
#
#         # Optional debug output
#         if configured_count > 0 and hasattr(self, "_debug_widget_config"):
#             print(
#                 f"🎯 Configured {configured_count} BlockNote widget(s) for user {self.user.username}",
#             )
#
#     def clean_aliases(self):
#         """Convert CSV string input to JSON string for storage"""
#         aliases = self.cleaned_data.get("aliases")
#
#         if not aliases:
#             return "[]"  # Empty JSON array
#
#         # Handle string input (CSV from forms)
#         if isinstance(aliases, str):
#             # Check if it's already JSON
#             try:
#                 parsed = json.loads(aliases)
#                 if isinstance(parsed, list):
#                     return aliases  # Already valid JSON
#             except (json.JSONDecodeError, ValueError):
#                 pass
#
#             # Treat as CSV and convert to JSON
#             alias_list = [
#                 alias.strip() for alias in aliases.split(",") if alias.strip()
#             ]
#             import json
#
#             return json.dumps(alias_list)
#
#         # Fallback for unexpected types
#         return "[]"
#
#
# class BlockNoteUserFormsetMixin:
#     """
#     Formset mixin to handle user context for forms containing BlockNote widgets.
#     Use this with Django formsets that contain forms with BlockNote widgets.
#
#     Usage:
#         MyFormSet = formset_factory(MyForm, formset=BlockNoteUserFormsetMixin)
#         formset = MyFormSet(user=request.user)
#     """
#
#     def __init__(self, *args, **kwargs):
#         """Initialize formset and pass user to all forms"""
#         # Extract user from kwargs BEFORE calling super()
#         self.user = kwargs.pop("user", None)
#         super().__init__(*args, **kwargs)
#
#     def get_form_kwargs(self, index):
#         """Pass user to individual forms in the formset"""
#         kwargs = (
#             super().get_form_kwargs(index)
#             if hasattr(super(), "get_form_kwargs")
#             else {}
#         )
#         if self.user:
#             kwargs["user"] = self.user
#         return kwargs
#
#     def _construct_form(self, i, **kwargs):
#         """Ensure user is passed when constructing forms"""
#         if self.user and "user" not in kwargs:
#             kwargs["user"] = self.user
#         return super()._construct_form(i, **kwargs)
#
#
# # Optional: Combined mixin for most common use case
# class BlockNoteFormMixin(BlockNoteUserFormMixin, forms.Form):
#     """
#     Complete form mixin combining BlockNote functionality.
#     Use this as a drop-in replacement for forms.Form or forms.ModelForm.
#
#     Usage:
#         class MyForm(BlockNoteFormMixin):
#             content = forms.CharField(widget=BlockNoteWidget())
#     """
#
#
# class BlockNoteModelFormMixin(BlockNoteUserFormMixin, forms.ModelForm):
#     """
#     Complete ModelForm mixin combining BlockNote functionality.
#     Use this as a drop-in replacement for forms.ModelForm.
#
#     Usage:
#         class MyModelForm(BlockNoteModelFormMixin):
#             class Meta:
#                 model = MyModel
#                 fields = ['content']
#                 widgets = {
#                     'content': BlockNoteWidget()
#                 }
#     """
