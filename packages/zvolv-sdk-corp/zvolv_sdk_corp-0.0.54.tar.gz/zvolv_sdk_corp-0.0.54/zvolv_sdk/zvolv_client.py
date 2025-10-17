import requests

from .modules.workspace import Workspace
from .modules.auth import Auth
from .modules.analytics import Analytics
from .modules.forms import Forms
from .modules.submissions import Submissions
from .modules.tasks import Tasks
from .modules.logger import Logger
from .modules.communications import Communications
from .modules.documents import Documents
from .modules.roles import Roles
from .modules.users import Users
from .modules.usergroups import UserGroups
from .modules.workflows import Workflows
from .modules.files import Files


class ZvolvClient:
    def __init__(self, base_url="http://zproxy", verify_ssl=True):

        if not base_url:
            raise ValueError("Base URL is required to initialize the client")

        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = verify_ssl  # Enable/Disable SSL verification
        self.logger = Logger()
        self._workspace_module = None
        self._auth_module = None
        self._analytics_module = None
        self._forms_module = None
        self._submissions_module = None
        self._tasks_module = None
        self._communications_module = None
        self._documents_module = None
        self._roles_module = None
        self._users_module = None
        self._usergroups_module = None
        self._workflows_module = None
        self._files_module = None

    @property
    def workspace(self):
        if not self._workspace_module:
            self._workspace_module = Workspace(self.session, self.logger, self.base_url)
        return self._workspace_module

    @property
    def auth(self):
        if not self._workspace_module or not self._workspace_module.workspace_instance:
            raise Exception('Workspace not initialized! Please use workspace.init() before calling auth methods')
        if not self._auth_module:
            self._auth_module = Auth(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._auth_module

    @property
    def analytics(self):

        self.validate()

        if not self._analytics_module:
            self._analytics_module = Analytics(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._analytics_module

    @property
    def forms(self):

        self.validate()

        if not self._forms_module:
            self._forms_module = Forms(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._forms_module

    @property
    def submissions(self):

        self.validate()

        if not self._submissions_module:
            self._submissions_module = Submissions(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._submissions_module

    @property
    def tasks(self):

        self.validate()

        if not self._tasks_module:
            self._tasks_module = Tasks(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._tasks_module

    @property
    def communications(self):

        self.validate()

        if not self._communications_module:
            self._communications_module = Communications(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._communications_module

    @property
    def documents(self):

        self.validate()

        if not self._documents_module:
            self._documents_module = Documents(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._documents_module

    @property
    def roles(self):

        self.validate()

        if not self._roles_module:
            self._roles_module = Roles(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._roles_module

    @property
    def users(self):

        self.validate()

        if not self._users_module:
            self._users_module = Users(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._users_module

    @property
    def usergroups(self):

        self.validate()

        if not self._usergroups_module:
            self._usergroups_module = UserGroups(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._usergroups_module

    @property
    def workflows(self):

        self.validate()

        if not self._workflows_module:
            self._workflows_module = Workflows(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._workflows_module

    @property
    def files(self):

        self.validate()

        if not self._files_module:
            self._files_module = Files(self.session, self.logger, self.base_url, self._workspace_module.workspace_instance)
        return self._files_module

    # Validate if workspace and user are initialized
    def validate(self):
        # Check if workspace is initialized 
        if self.workspace.workspace_instance is None:
            raise Exception('Workspace not initialized! Please use workspace.init() before calling auth methods')

        # Check if user is logged in
        if self.auth.user_instance is None:
            raise Exception('User not logged in! Please use auth.login() before calling *module methods')
