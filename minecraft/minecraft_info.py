import os
import boto3
import datetime
import json
from discord.embeds import Embed


class MinecraftInfo:

    STATUS_DICT = {
        'pending' : ':arrows_counterclockwise:起動中',
        'running' : ':green_circle:起動済み',
        'shutting-down' : ':warning:終了中:warning:',
        'terminated' : ':warning:終了済み:warning:',
        'stopping' : ':arrows_counterclockwise:停止中',
        'stopped' : ':red_circle:停止済み'
    }

    STATUS_MESSAGE = {
        'pending' : '更新ボタンを押してね',
        'running' : 'サーバーに接続できます（タイムラグあり）',
        'shutting-down' : 'このメッセージが表示されていないことを祈ります',
        'terminated' : 'このメッセージが表示されていないことを祈ります',
        'stopping' : ':更新ボタンを押してね',
        'stopped' : 'サーバーに接続するには起動ボタンを押してね'
    }

    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME')
    AWS_INSTANCE_ID = os.environ.get('AWS_INSTANCE_ID')
    output_embed: Embed

    instance: any
    pricing: any
    status: str

    def __init__(self):
        self.connect()
        #self.connect_pricing()

    def connect(self):
        self.instance = boto3.resource(
            'ec2',
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
            region_name=self.AWS_REGION_NAME
        ).Instance(self.AWS_INSTANCE_ID)
    
    def connect_pricing(self):
        self.pricing = boto3.client("pricing",
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY,
            region_name='us-east-1'
        )
    
    def fetch_price(self, instance_type: str) -> float:
        response = self.pricing.get_products(
            ServiceCode='AmazonEC2',
            Filters=[
              {
                'Type': 'TERM_MATCH',
                'Field': 'instanceType',
                'Value': instance_type
              },
              {
                  'Type': 'TERM_MATCH',
                  'Field': 'termType',
                  'Value': 'OnDemand'
              },
              {
                  'Type': 'TERM_MATCH',
                  'Field': 'location',
                  'Value': 'Asia Pacific (Tokyo)'
              },
              {
                  'Type': 'TERM_MATCH',
                  'Field': 'operatingSystem',
                  'Value': 'Linux'
              }
            ],
            MaxResults=1
        )
        response = json.loads(response['PriceList'][0])
        price_per_hour = 0
        for v in response['terms']['OnDemand'].values():
            for v2 in v['priceDimensions'].values():
                price_per_hour = float(v2['pricePerUnit']['USD'])
        return price_per_hour
    
    def update_record(self, domain_name, host):
        zone_id = os.environ.get('HOST_ZONE_ID')
        client = boto3.client('route53')
        batch = {
            "Comment": "optional comment about the changes in this change batch request",
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": domain_name,
                        "Type": "A",
                        "TTL": 300,
                        "ResourceRecords": [
                            {
                            "Value": host
                            }
                        ]
                    }
                }
            ]
        }
        response = client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch=batch
        )

    def fetch(self) -> Embed:
        self.connect()
        self.status = self.instance.state['Name']
        ipv4 = self.instance.public_ip_address
        instance_type = self.instance.instance_type
        embed: Embed = Embed(title='Minecraftサーバー情報', color=0x00b0f4, timestamp=datetime.datetime.utcnow())
        embed.add_field(name='状態', value=self.STATUS_DICT[self.status], inline=True)
        if ipv4:
            domain_name = os.environ.get('MC_DOMAIN_NAME')
            self.update_record(domain_name=domain_name, host=ipv4)
            embed.add_field(name='サーバー名', value='`{0}`'.format(domain_name), inline=True)
            embed.add_field(name='BlueMap', value='[こちら](http://{0}:8123)'.format(domain_name), inline=True)
            embed.set_footer(text='')
        if instance_type:
            embed.add_field(name='タイプ', value=instance_type, inline=True)
            #if self.status == 'running':
                #embed.add_field(name='料金', value='{0}＄/h'.format(self.fetch_price(instance_type)), inline=True)
        embed.set_footer(text=self.STATUS_MESSAGE[self.status])
        return embed
    
    def start(self) -> Embed:
        embed: Embed
        if self.status == 'stopped':
            try:
                self.instance.start()
                embed = self.fetch()
            except:
                embed = self.fetch()
                embed.add_field(name='エラーメッセージ', value='サーバーの起動に失敗しました。\n少し時間をおいてもう一度お試しください。', inline=False)
        else:
            embed = self.fetch()
            embed.add_field(name='エラーメッセージ', value='サーバーの起動はステータスが停止済みでないと行えません。', inline=False)
        return embed
    
    def stop(self) -> Embed:
        embed: Embed
        if self.status == 'running':
            self.instance.stop()
            embed = self.fetch()
        else:
            embed = self.fetch()
            embed.add_field(name='エラーメッセージ', value='サーバーの停止はステータスが起動済みでないと行えません。', inline=False)
        return embed


