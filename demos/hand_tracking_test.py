from xarp.server import run
from xarp.entities import Element, DefaultAssets
from xarp.gestures import PALM
from xarp.spatial import Transform, Vector3

def test(xarp, params):
    blob = Element(
        key="blob",
        asset=DefaultAssets.CUBE,
        transform=Transform(
            scale=Vector3.one() * .1
        )
    )

    stream = xarp.sense(hands=True)
    for frame in stream:
        hands = frame["hands"]
        if hands.right:
            blob.transform.position = hands.right[PALM].position
            xarp.update(blob)




if __name__== "__main__":
    run(test)