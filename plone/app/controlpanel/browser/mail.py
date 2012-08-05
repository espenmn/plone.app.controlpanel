import smtplib
import socket
import sys
from zope.component import getUtility
from z3c.form import button
from zope.site.hooks import getSite
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.utils import getToolByName
from Products.MailHost.MailHost import MailHostError
from Products.statusmessages.interfaces import IStatusMessage

from plone.app.registry.browser import controlpanel

from plone.app.controlpanel import _
from plone.app.controlpanel.interfaces import IMailSchema


class MailControlPanelForm(controlpanel.RegistryEditForm):

    id = "MailControlPanel"
    label = _(u"Mail settings")
    schema = IMailSchema

    @button.buttonAndHandler(
        _('label_smtp_test', default='Save and send test e-mail'),
        name='test')
    def handle_test_action(self, action):
        data = self.request.form
        # Save data first
        self.handle_edit_action.success(data)
        mailhost = getToolByName(self.context, 'MailHost')

        # XXX Will self.context always be the Plone site?
        fromaddr = self.context.getProperty('email_from_address')
        fromname = self.context.getProperty('email_from_name')

        message = ("Hi,\n\nThis is a test message sent from the Plone "
                   "'Mail settings' control panel. Your receipt of this "
                   "message (at the address specified in the Site 'From' "
                   "address field) indicates that your e-mail server is "
                   "working!\n\n"
                   "Have a nice day.\n\n"
                   "Love,\n\nPlone")
        email_charset = self.context.getProperty('email_charset')
        email_recipient, source = fromaddr, fromaddr
        subject = "Test e-mail from Plone"

        # Make the timeout incredibly short. This is enough time for most mail
        # servers, wherever they may be in the world, to respond to the
        # connection request. Make sure we save the current value
        # and restore it afterward.
        timeout = socket.getdefaulttimeout()
        try:
            socket.setdefaulttimeout(3)
            try:
                mailhost.send(message, email_recipient, source,
                              mfrom=fromname,
                              subject=subject,
                              charset=email_charset,
                              immediate=True)

            except (socket.error, MailHostError, smtplib.SMTPException):
                # Connection refused or timeout.
                log.exception('Unable to send test e-mail.')
                value = sys.exc_info()[1]
                msg = _(u'Unable to send test e-mail ${error}.',
                        mapping={'error': unicode(value)})
                IStatusMessage(self.request).addStatusMessage(
                    msg, type='error')
            else:
                IStatusMessage(self.request).addStatusMessage(
                    _(u'Success! Check your mailbox for the test message.'),
                    type='info')
        finally:
            # Restore timeout to default value
            socket.setdefaulttimeout(timeout)


class MailControlPanel(controlpanel.ControlPanelFormWrapper):
    form = MailControlPanelForm


def updateMailSettings(settings, event):
    portal = getSite()
    mailhost = getToolByName(portal, 'MailHost')
    mailhost.smtp_host = settings.smtp_host
    mailhost.smtp_port = settings.smtp_port
    mailhost.smtp_userid = settings.smtp_userid
    mailhost.smtp_pass = settings.smtp_pass
    getUtility(ISiteRoot).email_from_name = \
        settings.email_from_name
    getUtility(ISiteRoot).email_from_address = settings.email_from_address
