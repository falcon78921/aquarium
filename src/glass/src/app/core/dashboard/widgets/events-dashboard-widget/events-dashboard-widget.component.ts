import { Component } from '@angular/core';
import { marker as TEXT } from '@biesbjerg/ngx-translate-extract-marker';
import { Observable } from 'rxjs';

import { DatatableColumn } from '~/app/shared/models/datatable-column.type';
import { RelativeDatePipe } from '~/app/shared/pipes/relative-date.pipe';
import { Event, LocalNodeService } from '~/app/shared/services/api/local.service';

@Component({
  selector: 'glass-events-dashboard-widget',
  templateUrl: './events-dashboard-widget.component.html',
  styleUrls: ['./events-dashboard-widget.component.scss']
})
export class EventsDashboardWidgetComponent {
  data: Event[] = [];
  columns: DatatableColumn[];

  constructor(
    private localNodeService: LocalNodeService,
    private relativeDatePipe: RelativeDatePipe
  ) {
    this.columns = [
      {
        name: TEXT('Date'),
        prop: 'ts',
        pipe: this.relativeDatePipe
      },
      {
        name: TEXT('Severity'),
        prop: 'severity'
      },
      {
        name: TEXT('Message'),
        prop: 'message'
      }
    ];
  }

  updateData($data: Event[]) {
    this.data = $data;
  }

  loadData(): Observable<Event[]> {
    return this.localNodeService.events();
  }
}
