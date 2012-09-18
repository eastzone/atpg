// Some functions to (ab)use POST
function inject(){
  $.ajax({
    type: "POST",
    url: "inject",
    data: "Hello!",
  });
  
  $(".spinner").show();
  $("#button1").attr("disabled", "disabled");
}

function reset(){
  $.ajax({
    type: "POST",
    url: "reset",
    data: "Hello!",
  });
  
  $('svg image').attr("href", "images/router.png");
  $('svg image').tipsy("hide");
  $('.spinner').hide();
  $("#button1").removeAttr("disabled");
  $("#button3").removeAttr("disabled");
}

function detect(){
  $.ajax({
    type: "POST",
    url: "detect",
    data: "Hello!",
  });
  
  $(".spinner").show();
  $("#button3").attr("disabled", "disabled");
}

var layout = setMapLayout();
var force1;
var force2;

function map(){
  if ($("#button4").text() == "Map"){
    $("#button4").text("Regular");
    layout = setMapLayout();
    force1.resume();
    force2.resume();
    $(".paper").css("background-image", "url(images/campus.png)");
  }
  else {
    $("#button4").text("Map");
    layout = setRegularLayout();
    force1.resume();
    force2.resume();
    $(".paper").css("background-image", "");
  }
}

function setRegularLayout(){
  layout = {}
  layout['bbra_rtr'] = [1/4, 1/4];
  layout['bbrb_rtr'] = [3/4, 1/4];
  layout['boza_rtr'] = [1/15, 3/4];
  layout['bozb_rtr'] = [2/15, 3/4];
  layout['coza_rtr'] = [3/15, 3/4];
  layout['cozb_rtr'] = [4/15, 3/4];
  layout['goza_rtr'] = [5/15, 3/4];
  layout['gozb_rtr'] = [6/15, 3/4];
  layout['poza_rtr'] = [7/15, 3/4];
  layout['pozb_rtr'] = [8/15, 3/4];
  layout['roza_rtr'] = [9/15, 3/4];
  layout['rozb_rtr'] = [10/15, 3/4];
  layout['soza_rtr'] = [11/15, 3/4];
  layout['sozb_rtr'] = [12/15, 3/4];
  layout['yoza_rtr'] = [13/15, 3/4];
  layout['yozb_rtr'] = [14/15, 3/4];
  return layout;
}

function setMapLayout(){
  layout = {}
  layout['bbra_rtr'] = [0.2, 0.5];
  layout['bbrb_rtr'] = [0.42, 0.56];
  layout['boza_rtr'] = [0.22, 0.52];
  layout['bozb_rtr'] = [0.31, 0.48];
  layout['coza_rtr'] = [0.8, 0.6];
  layout['cozb_rtr'] = [0.75, 0.51];
  layout['goza_rtr'] = [0.35, 0.72];
  layout['gozb_rtr'] = [0.72, 0.56];
  layout['poza_rtr'] = [0.63, 0.35];
  layout['pozb_rtr'] = [0.38, 0.70];
  layout['roza_rtr'] = [0.22, 0.62];
  layout['rozb_rtr'] = [0.25, 0.25];
  layout['soza_rtr'] = [0.16, 0.34];
  layout['sozb_rtr'] = [0.83, 0.74];
  layout['yoza_rtr'] = [0.3, 0.4];
  layout['yozb_rtr'] = [0.32, 0.42];
  return layout;
}

function setTipsy(tag){
    $(tag + ' svg image').tipsy({ 
          //trigger: 'manual',
          gravity: $.fn.tipsy.autoNS,
          html: true, 
          fade: true,
          title: function(){
            return $(this).attr('id');
          },   
    });   
}

function start_demo(data_source, tag){
    var w = 800, h=800;        
    var image_size = 60;
    $(".paper").css("background-image", "url(images/campus.png)");

    var force = d3.layout.force()
        .charge(0)
        .linkDistance(10)
        .size([w, h])
        .gravity(0)
        .linkStrength(0);

    if (tag == "#topology"){
        force1 = force;
    }
    else{
        force2 = force;
    }

    var svg = d3.select(tag).append("svg:svg")
        .attr("width", w)
        .attr("height", h);

    d3.json(data_source, draw);
    
    setInterval(function(){
        $.ajax({ 
        url: data_source, 
        success: function(data){
            update_problem(data, tag);
        }, 
        dataType: "json",
        ifModified: true,
        });
    }, 2000);
    
    setTimeout("setTipsy(\'"+tag+"\')", 3000); 

    function update_problem(json, this_tag){  
      if (typeof json === "undefined") return
    
      var i;
      
      $(".spinner").hide();
      $("#button1").removeAttr("disabled");
      $("#button3").removeAttr("disabled");
      
      var problem_nodes = [];
      var routerSVG;
      for (i=0;i<json.nodes.length;i++){
          routerSVG = $(this_tag +' svg g #'+json.nodes[i].name);
          if(json.nodes[i].problems){
            problem_nodes.push(json.nodes[i]);
            routerSVG.attr("href", "images/red_router.png");
            routerSVG.attr("original-title", json.nodes[i].problems);
            routerSVG.attr("class", "failing");
          }
          else {
            routerSVG.attr("href", "images/router.png");
            routerSVG.attr("original-title", "I am OK! Thanks for asking.");
            routerSVG.attr("class", "passing");
          }
      }
      
      $(tag + ' svg image.failing').each(function(){
          var content = "<div class=router-report>";
          content += "<div class=report-name>"+$(this).attr('id')+":</div>"
          
          var strings = $(this).attr('original-title').split('$')
          
          var i=0;
          for (i=0; i<strings.length; i++){
            if (i % 3 == 0)
                content += "<div class=report-passing>" + "..." + "</div>";
            if (i % 3 == 1){
                content += "<div class=report-failing>" + strings[i] + "</div>";
            }
            else{
                content += "<div class=report-passing>" + strings[i] + "</div>";
            }
            if (i % 3 == 2)
                content += "<div class=report-passing>" + "..." + "</div>";
          }
          
          content += "</div>";
          $(this).fancybox({
              'type' : 'html',
              'content' : content,
          });
      });    
      
      $(tag + ' svg image.passing').each(function(){
          content = "<div class=router-report>";
          content += "<div class=report-name>"+$(this).attr('id')+":</div>"
          content += "<div class=report-failing>I'm healthy!</div>"
          content += "</div>";
          $(this).fancybox({
              'type' : 'html',
              'content' : content,
          });
      });    
          
      var problem_links = [];
      for (i=0;i<json.links.length;i++){
          if(json.links[i].problems){
            problem_links.push(json.links[i]);
            $(this_tag +' svg #'+json.links[i].name).attr("stroke", "red");
          }
          else{
            $(this_tag +' svg #'+json.links[i].name).attr("stroke", "green");
          }
      }
    }

    function draw(json) {
      var link = svg.selectAll("line")
          .data(json.links)
        .enter().append("svg:line")
          .attr("stroke","green")
          .attr("stroke-width",1)
          .attr("id", function(d){return d.name;});

      var node = svg.selectAll("g.node")
          .data(json.nodes)
        .enter().append("svg:g")
          .attr("class", "node")
          .call(force.drag);

      node.append("svg:image")
          .attr("xlink:href", "images/router.png")
          .attr("width", image_size + "px")
          .attr("height", image_size + "px")
          .attr("id", function(d){return d.name;})
          ;

      force
          .nodes(json.nodes)
          .links(json.links)
          .on("tick", tick)
          .start();
          

      function tick(e) {
        node.attr("transform", function(d) {return returnToPosition(d, e);});
        
        link.attr("x1", function(d) { return d.source.x+image_size/2; })
            .attr("y1", function(d) { return d.source.y+image_size/2; })
            .attr("x2", function(d) { return d.target.x+image_size/2; })
            .attr("y2", function(d) { return d.target.y+image_size/2; });
      }
      
      function returnToPosition(d, e){
        var x=0, y=0;
        var damper = 1;
        var alpha = e.alpha;
        var router_name = d.name;
        
        x = fixPoint(d.x, w * layout[router_name][0], alpha, damper);
        y = fixPoint(d.y, h * layout[router_name][1], alpha, damper);

        d.x = x;
        d.y = y;
        return "translate(" + x + "," + y + ")";    
      }
      
      function fixPoint(current, target, alpha, damper){
        target = target - image_size / 2;
        if (target-current < 1 && target-current > -1){
            return target;
        }
        return current + (target - current) * damper * alpha;
      }
      
      function normalize(x, lower_limit, upper_limit) {
        if (x < lower_limit) return lower_limit;
        if (x > upper_limit) return upper_limit;
        return x;
      }
    }
}
