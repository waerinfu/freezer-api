# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2014 IBM Corp.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_db.sqlalchemy import models
from oslo_utils import timeutils
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from sqlalchemy import BLOB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship


BASE = declarative_base()


class FreezerBase(models.TimestampMixin,
                  models.ModelBase):
    """Base class for Freezer Models."""

    __table_args__ = {'mysql_engine': 'InnoDB'}

    deleted_at = Column(DateTime)
    deleted = Column(Boolean, default=False)
    backup_metadata = None

    @staticmethod
    def delete_values():
        return {'deleted': True,
                'deleted_at': timeutils.utcnow()}

    def delete(self, session):
        """Delete this object."""
        updated_values = self.delete_values()
        self.update(updated_values)
        self.save(session=session)
        return updated_values


class Client(BASE, FreezerBase):
    """Represents a scheduler of the freezer action."""

    __tablename__ = 'clients'
    id = Column(String(255), primary_key=True)
    project_id = Column(String(36), nullable=False)
    user_id = Column(String(64), nullable=False)
    client_id = Column(String(255), nullable=False)
    hostname = Column(String(128))
    description = Column(String(255))
    uuid = Column(String(36), nullable=False)


class Action(BASE, FreezerBase):
    """Represents freezer action."""
    # The field backup_metadata is json, including :
    # hostname ,snapshot ,storage ,dry_run , lvm_auto_snap, lvm_dirmount,
    # lvm_snapname max_level , max_priority, max_segment_size , mode,
    # mysql_conf, path_to_backup,  remove_older_than restore_abs_path
    # restore_from_host, ssh_host , ssh_key , ssh_username, ssh_port , proxy
    # no_incremental, overwrite , nova_inst_id , engine_name
    # restore_from_date , command , incremental

    __tablename__ = 'actions'
    id = Column(String(36), primary_key=True)
    action = Column(String(255), nullable=False)
    project_id = Column(String(36), nullable=False)
    user_id = Column(String(64), nullable=False)
    mode = Column(String(255))
    src_file = Column(String(255))
    backup_name = Column(String(255))
    container = Column(String(255))
    timeout = Column(Integer)
    priority = Column(Integer)
    max_retries_interval = Column(Integer, default=6)
    max_retries = Column(Integer, default=5)
    mandatory = Column(Boolean, default=False)
    log_file = Column(String(255))
    backup_metadata = Column(Text)


class Job(BASE, FreezerBase):
    """Represents freezer job."""

    __tablename__ = 'jobs'
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False)
    scheduling = Column(Text)
    description = Column(String(255))


class Session(BASE, FreezerBase):
    """Represents freezer session."""

    __tablename__ = 'sessions'
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False)
    scheduling = Column(Text)
    policy = Column(String(255))


class ActionReport(BASE, FreezerBase):
    __tablename__ = 'action_reports'
    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False)
    user_id = Column(String(64), nullable=False)
    result = Column(String(255))
    time_elapsed = Column(String(255))
    report_date = Column(TIMESTAMP)
    log = Column(BLOB)


class JobAttachment(BASE, FreezerBase):
    __tablename__ = 'job_attachments'
    id = Column(String(36), primary_key=True)
    client_id = Column(String(255), ForeignKey('clients.id'), nullable=False)
    job_id = Column(String(36), ForeignKey('jobs.id'), nullable=False)
    session_id = Column(String(36), ForeignKey('sessions.id'), nullable=False)
    project_id = Column(String(36), nullable=False)
    event = Column(String(255))
    status = Column(String(255))
    current_pid = Column(Integer)
    client = relationship(Client, backref='job_attachments',
                          foreign_keys=client_id,
                          primaryjoin='and_('
                          'JobAttachment.client_id == Client.id,'
                          'JobAttachment.deleted == False)')
    job = relationship(
        Job,
        backref='job_attachments',
        foreign_keys=job_id,
        primaryjoin='and_('
        'JobAttachment.job_id == Job.id,'
        'JobAttachment.deleted == False)')
    session = relationship(Session, backref='job_attachments',
                           foreign_keys=session_id,
                           primaryjoin='and_('
                           'JobAttachment.session_id == Session.id,'
                           'JobAttachment.deleted == False)')


def register_models(engine):
    _models = (Client, Action, Job, Session,
               ActionReport, JobAttachment)
    for _model in _models:
        _model.metadata.create_all(engine)


def unregister_models(engine):
    _models = (Client, Action, Job, Session,
               ActionReport, JobAttachment)
    for _model in _models:
        _model.metadata.drop_all(engine)


def get_tables(engine):
    from sqlalchemy import MetaData
    _meta = MetaData()
    _meta.reflect(engine)
    return _meta.tables.keys()
