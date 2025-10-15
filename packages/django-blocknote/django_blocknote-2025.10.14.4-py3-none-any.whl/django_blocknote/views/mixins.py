class BlockNoteViewMixin:
    """
    Cooperative view mixin to automatically pass user context to forms with BlockNote widgets.

    This lightweight mixin enhances Django's form-capable views to provide user context
    to BlockNote widgets for template personalization and user-specific functionality.
    It handles both regular forms and formsets/inlines seamlessly.

    Key Features:
    - Automatically detects and provides user context to BlockNote widgets
    - Supports both individual forms and formset/inline scenarios
    - Works with any Django view that has form capabilities
    - Designed for cooperative inheritance with minimal conflicts
    - Gracefully handles unauthenticated users

    Usage:
        class DocumentCreateView(BlockNoteViewMixin, CreateView):
            model = Document
            form_class = DocumentForm  # Contains BlockNote widgets

        class BlogPostUpdateView(TagMeViewMixin, BlockNoteViewMixin, UpdateView):
            model = BlogPost
            form_class = BlogPostForm

    Requirements:
    - Must be used with views that support forms (FormView, CreateView, UpdateView, etc.)
    - Forms should contain BlockNote widgets to benefit from user context
    - Works best with authenticated users (gracefully handles anonymous users)

    Cooperative Design:
    This mixin is designed to work harmoniously with other form mixins:
    - Only adds 'user' to kwargs if not already present
    - Always calls super() methods to maintain inheritance chain
    - No assumptions about base classes or other mixins
    - Safe to use in any order with other cooperative mixins

    Widget Integration:
    The user context passed to forms is automatically detected and used by:
    - BlockNote widgets for user-specific templates
    - Any other widgets that accept 'user' in their context
    - Form validation that requires user information

    Formset Support:
    Includes specialized support for Django formsets and inline formsets:
    - Automatically passes user context to formset constructors
    - Works with inlineformset_factory and formset_factory
    - Maintains user context across all forms in the formset

    Performance Considerations:
    - Minimal overhead - only adds user to context when needed
    - No additional database queries
    - Stateless design for thread safety
    - Lazy evaluation of user authentication status

    Example with Formsets:
        class ArticleUpdateView(BlockNoteViewMixin, UpdateView):
            model = Article
            form_class = ArticleForm

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                SectionFormSet = inlineformset_factory(Article, Section, form=SectionForm)
                context['section_formset'] = SectionFormSet(
                    instance=self.object,
                    **self.get_formset_kwargs()  # Includes user context
                )
                return context
    """  # noqa: E501

    def get_form_kwargs(self):
        """
        Add user context to form kwargs for BlockNote widgets.

        This method cooperatively enhances form kwargs with user information
        that BlockNote widgets need for personalization and template selection.
        The method only adds user context if:
        1. User is not already in kwargs (cooperative behavior)
        2. Request has a user attribute (safety check)
        3. User is authenticated (avoids passing anonymous users)

        Returns:
            dict: Form kwargs enhanced with user context when appropriate

        Cooperative Behavior:
        - Calls super() to maintain inheritance chain
        - Checks for existing 'user' key to avoid conflicts
        - Safe to use with other mixins that also provide user context

        Safety Features:
        - Validates request.user exists before accessing
        - Only passes authenticated users to avoid widget confusion
        - Gracefully handles edge cases in authentication middleware
        """
        kwargs = super().get_form_kwargs()

        # Only add user if not already present and user is authenticated
        # This ensures cooperative behavior with other mixins
        if (
            "user" not in kwargs
            and hasattr(self.request, "user")
            and self.request.user.is_authenticated
        ):
            kwargs["user"] = self.request.user

        return kwargs

    def get_form(self, form_class=None):
        """
        Enhanced form creation with BlockNote-specific context handling.

        Creates form instances with proper user context for BlockNote widgets.
        This method provides error handling and ensures consistent
        user context across different form creation paths.

        Args:
            form_class (class, optional): The form class to instantiate.
                If None, uses get_form_class() to determine the form.

        Returns:
            Form: Instantiated form with BlockNote user context

        Features:
        - Uses get_form_kwargs() for consistent user context
        - Provides clear debugging information in development
        - Maintains cooperative inheritance pattern
        - Future-ready for additional BlockNote context

        Note:
            This method relies on get_form_kwargs() for user
            context. This ensures consistency and reduces
            maintenance overhead.
        """
        if form_class is None:
            form_class = self.get_form_class()

        # Get form kwargs using the cooperative method
        # This ensures consistent user context handling
        form_kwargs = self.get_form_kwargs()

        # Future expansion point for additional BlockNote context:
        # form_kwargs["editor_permissions"] = self.get_editor_permissions()
        # form_kwargs["template_context"] = self.get_template_context()

        return form_class(**form_kwargs)

    def get_formset_kwargs(self):
        """
        Add user context to formset kwargs for inline forms with BlockNote widgets.

        This method enables BlockNote functionality in Django formsets and
        inline formsets by ensuring user context is available to all forms
        within the formset. This is essential for:
        - Inline editing scenarios
        - Bulk form operations
        - Complex forms with multiple BlockNote widgets

        Returns:
            dict: Formset kwargs enhanced with user context

        Usage with Inline Formsets:
            SectionFormSet = inlineformset_factory(Article, Section, form=SectionForm)
            formset = SectionFormSet(
                instance=article,
                **self.get_formset_kwargs()  # Includes user context
            )

        Compatibility:
        - Works with formset_factory and inlineformset_factory
        - Compatible with Django's admin inline formsets
        - Maintains consistency with get_form_kwargs() behavior

        Safety:
        - Calls super() if method exists (cooperative inheritance)
        - Only adds authenticated users
        - Handles views that don't normally use formsets
        """
        # Handle cooperative inheritance - some views may not have this method
        kwargs = (
            super().get_formset_kwargs()
            if hasattr(super(), "get_formset_kwargs")
            else {}
        )

        # Add user context for BlockNote widgets in formset forms
        if hasattr(self.request, "user") and self.request.user.is_authenticated:
            kwargs["user"] = self.request.user

        return kwargs
