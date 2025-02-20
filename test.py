from utils.options import get_undertakers


if __name__ == '__main__':
  undertakers = get_undertakers()
  print(undertakers)
  print(undertakers.get(10).name)