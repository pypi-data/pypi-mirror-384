import matplotlib.pyplot as plt

def sign(x):
  if x >= 0:
    return 1
  else:
    return -1

def graph_nn(layer_neurons, neuron_parameters=[]):
  """

    Draws a simple diagram of a complete neural network

    Parameters:
    -----------
    layer_neurons : list of int
        Number of neurons for each layer [input, hidden1, hidden2, ..., output]


    Example:
    --------
    >>> graph_nn(layer_neurons = [3, 3, 2, 3])
    
  """

  neuroni_lista = []
  d = max(layer_neurons)*0.02
  # LOOP SUI LAYER
  for i in range(0, len(layer_neurons)):

    # Colori e gestione testo (input = arancione, output = azzurro, hidden = verde)
    if i == 0:
      color = "orange"
      value_text = True
    elif i == len(layer_neurons) - 1:
      color = "cyan"
      value_text = False
    else:
      color = "green"
      value_text = False

    # Caso: layer con numero pari di neuroni
    if layer_neurons[i] % 2 == 0:
      number_of_neurons = layer_neurons[i]
      for neuron in range(int(-number_of_neurons/2), int(+number_of_neurons/2 + 1)):
        if neuron != 0:
          coord = sign(neuron)*0.5 + neuron-sign(neuron)
          # Disegno neurone
          plt.scatter(i, coord, color=color, s=500, zorder=2)
          neuroni_lista.append((i, coord))

    # Caso: layer con numero dispari di neuroni
    if layer_neurons[i] % 2 == 1:
      number_of_neurons = layer_neurons[i]
      for neuron in range(int(-layer_neurons[i]/2), int(+layer_neurons[i]/2 + 1)):
        coord = neuron
        # Disegno neurone
        plt.scatter(i, coord, color=color, s=500, zorder=2)
        neuroni_lista.append((i, coord))

  # DISEGNO CONNESSIONI FRA NEURONI
  for i in range(0, len(layer_neurons)-1):
    actual_neurons = [t for t in neuroni_lista if t[0] == i]
    next_neurons = [t for t in neuroni_lista if t[0] == i+1]
    for neur1 in actual_neurons:
      x1, y1 = neur1
      for neur2 in next_neurons:
        x2, y2 = neur2
        plt.plot([x1,x2], [y1,y2], color="gray", zorder=1)

  plt.axis("off")
  plt.show()
