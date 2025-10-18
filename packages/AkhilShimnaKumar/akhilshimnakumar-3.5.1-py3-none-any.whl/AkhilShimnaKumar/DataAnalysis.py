@staticmethod
def split(x, y, split):
  split_index = int(len(x) * split)
  return x[:split_index], x[split_index:], y[:split_index], y[split_index:]

@staticmethod
def normalise(x):

  mean = sum(x)/len(x)
  variance = sum((i - mean) ** 2 for i in x) / len(x)
  std =  variance ** 0.5

  for i in range(len(x)):
    x[i] = (x[i]-mean)/std
  return x
