class Vigenere:
  def __init__(self):
    self.key = None
    self.decrypt = False

  def set_key(self, key):
    self.key = key

  def set_decrypt(self, decrypt):
    self.decrypt = decrypt

  def classifier(self, char):
      if (65<= ord(char) <= 90):
        return True, True
      elif (97<= ord(char) <= 122):
        return True, False
      else:
        return False, False

  def calculate_shift(self, counter):
    key_index = counter % len(self.key)
    shift_character = self.key[key_index]
    if 65<= ord(shift_character) <= 90:
      shift = ord(shift_character) - 65
    elif 97<= ord(shift_character) <= 122:
      shift = ord(shift_character) - 97
    if self.decrypt:
      shift *= -1
    return shift

    
  def cipher(self, message, key="SECRET", decrypt=False):
    self.set_key(key)
    self.set_decrypt(decrypt)
    

    ciphered_message = ""
    counter = 0
    for old_char in message:
      new_char = ""

      if not self.classifier(old_char)[0]:
        new_char = old_char
      else:
        shift = self.calculate_shift(counter)
        if self.classifier(old_char)[1]:
          new_char = chr(((ord(old_char)-65+shift)%26)+65)
        else:
          new_char = chr(((ord(old_char)-97+shift)%26)+97)
        counter += 1
      
      ciphered_message += new_char
      
    return ciphered_message
