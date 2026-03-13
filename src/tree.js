import f3 from 'family-chart';

export function main(data) {
    const f3Chart = f3.createChart('#FamilyChart', data);

    f3Chart
      .setCardHtml()
      .setCardDisplay([["name"],
                       ["birth"]]);

    f3Chart.updateTree({initial: true});
}
