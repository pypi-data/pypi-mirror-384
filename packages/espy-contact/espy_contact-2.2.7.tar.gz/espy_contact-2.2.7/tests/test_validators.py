"""Copyright 2024 Everlasting Systems and Solutions LLC (www.myeverlasting.net).
All Rights Reserved.

No part of this software or any of its contents may be reproduced, copied, modified or adapted, without the prior written consent of the author, unless otherwise indicated for stand-alone materials.

For permission requests, write to the publisher at the email address below:
office@myeverlasting.net

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
from espy_contact.schema.campus import Asset
from espy_contact.util.enums import StatusEnum
def test_asset_images():
    asset = {
        'title': 'Asset Title',
        'description': 'Asset Description',
        'created_by': 'john@example.com',
        'status': StatusEnum.NEW,
        'images': 'image1.jpg,image2.jpg,image3.jpg',
    }
    asset = Asset(**asset)
    assert asset.images == ['image1.jpg', 'image2.jpg', 'image3.jpg']