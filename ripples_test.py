import time

import effects

def main():
    effect = effects.RipplesEffect(auto_reset_frames=0)
    effect.add_config()
    effect.add_config()
    effect.add_config()

    for i in range(5):
        effect.drawFrame()

    start = time.time()
    for i in range(100):
        effect.drawFrame()
    print 'drawn 100 frames in', (time.time()-start)


if __name__ == '__main__':
    main()
