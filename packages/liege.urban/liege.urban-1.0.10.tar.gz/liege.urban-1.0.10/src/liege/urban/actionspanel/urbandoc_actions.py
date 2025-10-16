# -*- coding: utf-8 -*-

from imio.actionspanel.browser.views import ActionsPanelView


class UrbanDocActionsPanelView(ActionsPanelView):
    """
    By default only show workflow, edit, and delete actions
    on urban objects.
    """
    def __init__(self, context, request):
        super(UrbanDocActionsPanelView, self).__init__(context, request)

        self.SECTIONS_TO_RENDER = ('renderTransitions', 'renderEdit', 'renderOwnDelete',)
        self.IGNORABLE_ACTIONS = ('cut', 'paste', 'rename', 'copy')

    def __call__(self,
                 useIcons=True,
                 showTransitions=True,
                 appendTypeNameToTransitionLabel=False,
                 showEdit=True,
                 showOwnDelete=True,
                 showActions=True,
                 showAddContent=False,
                 showHistory=False,
                 showHistoryLastEventHasComments=False,
                 **kwargs):

        return super(UrbanDocActionsPanelView, self).__call__(
            useIcons=useIcons,
            showTransitions=showTransitions,
            appendTypeNameToTransitionLabel=False,
            showEdit=showEdit,
            showOwnDelete=showOwnDelete,
            showActions=showActions,
            showAddContent=showAddContent,
            showHistory=showHistory,
            showHistoryLastEventHasComments=showHistoryLastEventHasComments,
            **kwargs
        )
