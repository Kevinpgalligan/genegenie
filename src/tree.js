import f3 from 'family-chart';
import * as d3 from 'd3';

var f3Chart;

export function zoom(zoomFactor) {
  f3.handlers.manualZoom({ svg: f3Chart.svg, amount: zoomFactor });
}

export function main(data, maybe_person_id) {
    f3Chart = f3.createChart('#FamilyChart', data)
	  .setShowSiblingsOfMain(true)
      .setSingleParentEmptyCard(false);
	if (maybe_person_id) {
	  f3Chart.updateMainId(maybe_person_id);
	}

    f3Chart
      .setCardHtml()
	  .setCardInnerHtmlCreator(d => {
      	return `<div class="card-inner">
        <div>${d.data.data["name"]}<br/>b. ${d.data.data["birth"]}<br/>d. ${d.data.data["death"]}
		<br/><a href="/person/${d.data.id}.html" target="_blank">↪ view</a></div>
      	</div>`
    	})
	  .setOnCardClick((mouse_event, d) => {
		  // Based on CardHtml.onCardClickDefault, difference is that tree_position is specified.
		  f3Chart.updateMainId(d.data.id);
    	  f3Chart.updateTree({tree_position: 'main_to_middle'});
		})
      .setMiniTree(true);

    f3Chart.updateTree({initial: true});
	// The view properties would be overridden on the initial render, so call updateTree again.
	f3Chart.updateTree({initial: false, tree_position: 'main_to_middle', scale: 1})
}
