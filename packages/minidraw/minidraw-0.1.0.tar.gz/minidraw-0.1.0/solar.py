from minidraw import Drawing

d = Drawing()

d.circle((0.00, 0.00), 20.00)
d.text((0.00, 30.00), 'Sun')
d.circle((0.00, 0.00), 40.00)
d.circle((0.00, 0.00), 70.00)
d.circle((0.00, 0.00), 100.00)
d.circle((28.28, 28.28), 3.00)
d.text((28.28, 37.28), 'Mercury')
d.circle((-35.00, 60.62), 5.00)
d.text((-35.00, 71.62), 'Venus')
d.circle((-93.97, -34.20), 6.00)
d.text((-93.97, -22.20), 'Earth')

d.render_to_file("output.svg")