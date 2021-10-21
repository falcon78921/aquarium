/*
 * Project Aquarium's frontend (glass)
 * Copyright (C) 2021 SUSE, LLC.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 */
import { Component, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';

import { bytesToSize } from '~/app/functions.helper';
import { Icon } from '~/app/shared/enum/icon.enum';
import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { LocalNodeService } from '~/app/shared/services/api/local.service';
import { NotificationService } from '~/app/shared/services/notification.service';

type TableEntry = {
  qualified: boolean;
  name: string;
  actual: string;
  min: string;
  error: string;
};

@Component({
  selector: 'glass-install-welcome-page',
  templateUrl: './install-welcome-page.component.html',
  styleUrls: ['./install-welcome-page.component.scss']
})
export class InstallWelcomePageComponent implements OnInit {
  @ViewChild('qualifiedColTpl', { static: true })
  public qualifiedColTpl!: TemplateRef<any>;

  @ViewChild('nodeConfigColTpl', { static: true })
  public nodeConfigColTpl!: TemplateRef<any>;

  public icons = Icon;
  public status: TableEntry[] = [];
  public checked = false;
  public qualified = false;
  public statusColumns: DatatableColumn[] = [];

  constructor(
    private localNodeService: LocalNodeService,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    this.statusColumns.unshift(
      {
        name: TEXT('Qualified'),
        prop: 'qualified',
        cellTemplate: this.qualifiedColTpl,
        unsortable: true
      },
      {
        name: TEXT('Name'),
        prop: 'name'
      },
      {
        name: TEXT('Node Configuration'),
        prop: 'actual',
        cellTemplate: this.nodeConfigColTpl
      },
      {
        name: TEXT('Minimum requirement'),
        prop: 'min'
      },
      {
        name: TEXT('Description'),
        prop: 'error'
      }
    );
  }

  checkRequirements(): void {
    this.localNodeService.status().subscribe(
      (res) => {
        this.checked = true;
        if (res.localhost_qualified) {
          const hostQualified = res.localhost_qualified;
          this.qualified = res.localhost_qualified.all_qualified;
          this.status = [
            {
              qualified: hostQualified.cpu_qualified.qualified,
              name: 'CPU',
              actual: String(hostQualified.cpu_qualified.actual_threads),
              min: String(hostQualified.cpu_qualified.min_threads),
              error: hostQualified.cpu_qualified.error
            },
            {
              qualified: hostQualified.mem_qualified.qualified,
              name: 'Memory',
              actual: bytesToSize(hostQualified.mem_qualified.actual_mem),
              min: bytesToSize(hostQualified.mem_qualified.min_mem),
              error: hostQualified.mem_qualified.error
            },
            {
              qualified: hostQualified.root_disk_qualified.qualified,
              name: 'Disk',
              actual: bytesToSize(hostQualified.root_disk_qualified.actual_disk),
              min: bytesToSize(hostQualified.root_disk_qualified.min_disk),
              error: hostQualified.root_disk_qualified.error
            }
          ];
        }
      },
      (err) => {
        err.preventDefault();
        this.notificationService.show(err.message, {
          type: 'error'
        });
      }
    );
  }
}