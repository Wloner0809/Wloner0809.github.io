<!--
Publications are rendered in two groups from _data/publications.yml:
  selected — always visible (first-author / co-first / technical report)
  others   — inside a collapsible <details> ("Other Publications")
Each entry is rendered by _includes/pub-entry.html. Live citation counts are
fetched once from the Google Scholar crawler JSON for all .total_citation_mtl.
-->
<h1 id="publications"></h1>

<h2 style="margin: 30px 0px -15px;" class="reveal">Publications <temp style="font-size:15px;">[</temp><a href="https://scholar.google.com/citations?user=w55OAegAAAAJ&hl=en" target="_blank" style="font-size:15px;">Google Scholar</a><temp style="font-size:15px;">]</temp><temp style="font-size:15px;">[</temp><a href="https://www.researchgate.net/profile/Yu-Wang-1162" target="_blank" style="font-size:15px;">ResearchGate</a><temp style="font-size:15px;">]</temp></h2>


<div class="publications">
<ol class="bibliography">
{% for link in site.data.publications.selected %}
{% include pub-entry.html link=link %}
{% endfor %}
</ol>

{% if site.data.publications.others and site.data.publications.others.size > 0 %}
<details class="pub-more">
<summary>Other Publications</summary>
<ol class="bibliography">
{% for link in site.data.publications.others %}
{% include pub-entry.html link=link inline_citation=true %}
{% endfor %}
</ol>
</details>
{% endif %}
</div>

<script>
  $(document).ready(function () {
      var gsDataBaseUrl = 'https://raw.githubusercontent.com/Wloner0809/Wloner0809.github.io/main/';
      $.getJSON(gsDataBaseUrl + "google_scholar_crawler/results/gs_data.json", function (data) {
          var citationEles = document.getElementsByClassName('total_citation_mtl');
          Array.prototype.forEach.call(citationEles, function(element) {
              var citationKey = element.getAttribute('data-citation');
              if (data && data['publications'] && data['publications'][citationKey]) {
                  var numCitations = data['publications'][citationKey]['num_citations'];
                  element.innerHTML = numCitations || '0';
              } else {
                  element.innerHTML = 'N/A';
              }
          });
      }).fail(function(jqXHR, textStatus, errorThrown) {
          console.log('Failed to load citation data:', textStatus, errorThrown);
          var citationEles = document.getElementsByClassName('total_citation_mtl');
          Array.prototype.forEach.call(citationEles, function(element) {
              element.innerHTML = 'N/A';
          });
      });
  });
</script>
